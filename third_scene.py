import pygame
import math
import random
from match_scene import MatchScene, px2m, m2px, SW, SH, PPM
from factory import RocketFactory

# Scene constants
GROUND_Y   = 520
GOAL_W     = 160
GOAL_H     = 320
GOAL_POST  = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H + 30
JENNY_START = (SW - 200, GROUND_Y - 60)
JENNY_INDICATOR_POS = (SW - 10, 10)

# Flash
FLASH_STUN_DURATION       = 2000   # ms
FLASH_COLOR               = (255, 255, 240)
FLASH_STUN_TXT_COLOR      = (255, 230, 0)
FLASH_FONT_SIZE           = 20
FLASH_OVERLAY_ALPHA       = 210
FLASH_HOLD_BEFORE_FADE_MS = 2000

# Sunglasses power-up duration in ms
SUNGLASSES_DURATION  = 10000
SUNGLASSES_COLOR     = (0, 200, 255)
SUNGLASSES_HUD_COLOR = (0, 220, 180)

# Trapdoors
TRAPDOOR_W                    = 80    # px
TRAPDOOR_H                    = 14    # px
TRAPDOOR_COLOR                = (50, 50, 70)
TRAPDOOR_BORDER_COLOR         = (80, 80, 120)
TRAPDOOR_ACTIVE_COLOR         = (255, 80, 0)
TRAPDOOR_LAUNCH_VY            = -37.0
TRAPDOOR_ACTIVE_MS            = 400
TRAPDOOR_MAX_COUNT            = 2
TRAPDOOR_SPAWN_INTERVAL_RANGE = (3000, 7000)   # ms between spawn attempts
TRAPDOOR_LIFETIME_RANGE       = (5000, 10000)  # ms each trapdoor stays on field
TRAPDOOR_FIELD_MARGIN         = 40             # px buffer from each goal


class ThirdScene(MatchScene):
    """
    Scene: La Jenny.
    Mechanics:
        - Jenny is faster than the player.
        - Every ~20s she launches a headlight flash that blinds the player for 2s (unless wearing sunglasses).
        - Up to 2 trapdoors spawn at random ground positions, launching player and boss upwards (not the ball).
        - Power-up: Sunglasses: protect from the flash while active.
    """

    def _get_config(self):
        return {
            'ground_y':      GROUND_Y,
            'player_start':  (200, GROUND_Y - 100),
            'ball_start':    (SW // 2, GROUND_Y - 220),
            'gravity':       (0, 35),
            'player_speed':  12.0,
            'player_jump':   -28.0,
            'ground_blend':  0.35,
            'air_blend':     0.12,
            'player_hh':     3.5,
            'goal_pause_ms': 2000,
        }

    def _init_extras(self):
        # Boss Jenny
        self.boss = RocketFactory.create_element(
            "boss", self.world, JENNY_START, subtipo='lajenny')
        self.grupo_sprites.add(self.boss)

        # Flash
        self.player_flashed = False
        self.flash_stun_timer = 0
        self.flash_font = pygame.font.SysFont('Arial', FLASH_FONT_SIZE, bold=True)
        self.jenny_font = pygame.font.SysFont('Arial', 18, bold=True)
        self._flash_overlay_alpha = 0
        self._flash_hold_timer = 0
        self._flash_protected_timer = 0
        self._sunglasses_timer = 0

        # Trapdoors
        self._trapdoors = []
        self._spawn_timer = random.randint(1000, 2000)
        self._spawn_trapdoor()  # place one immediately at the start

    # ─── TRAPDOOR LOGIC ──────────────────────────────────────

    def _random_trapdoor_x(self):
        """Returns a random center X in the playfield, away from goals and existing trapdoors."""
        x_min = GOAL_W + TRAPDOOR_FIELD_MARGIN + TRAPDOOR_W // 2
        x_max = SW - GOAL_W - TRAPDOOR_FIELD_MARGIN - TRAPDOOR_W // 2
        for _ in range(20):
            cx = random.randint(x_min, x_max)
            if all(abs(cx - td['cx']) > TRAPDOOR_W * 1.5 for td in self._trapdoors):
                return cx
        return None

    def _spawn_trapdoor(self):
        """Creates a new trapdoor at a random position if under the max count."""
        if len(self._trapdoors) >= TRAPDOOR_MAX_COUNT:
            return
        cx_px = self._random_trapdoor_x()
        if cx_px is None:
            return
        x_px = cx_px - TRAPDOOR_W // 2
        y_px = GROUND_Y - TRAPDOOR_H
        rect = pygame.Rect(x_px, y_px, TRAPDOOR_W, TRAPDOOR_H)
        sensor_body = RocketFactory.create_trapdoor_sensor(
            self.world, cx_px, y_px, TRAPDOOR_W, TRAPDOOR_H, id(rect)
        )
        self._trapdoors.append({
            'rect':         rect,
            'cx':           cx_px,
            'sensor_body':  sensor_body,
            'active':       False,
            'active_timer': 0,
            'lifetime':     random.randint(*TRAPDOOR_LIFETIME_RANGE),
        })

    def _update_trapdoor_lifetimes(self, delta_time):
        """Counts down lifetimes, removes expired trapdoors, and fires the spawn timer."""
        surviving = []
        for td in self._trapdoors:
            td['lifetime'] -= delta_time
            if td['lifetime'] <= 0:
                RocketFactory.destroy_body(self.world, td.get('sensor_body'))
            else:
                surviving.append(td)
        self._trapdoors = surviving

        self._spawn_timer -= delta_time
        if self._spawn_timer <= 0:
            self._spawn_trapdoor()
            self._spawn_timer = random.randint(*TRAPDOOR_SPAWN_INTERVAL_RANGE)

    def _destroy_trapdoors(self):
        for td in self._trapdoors:
            body = td.get('sensor_body')
            if body:
                RocketFactory.destroy_body(self.world, body)
                td['sensor_body'] = None
        self._trapdoors = []

    def _update_trapdoors(self, delta_time):
        player_body = self.jugador.body
        boss_body = self.boss.body if hasattr(self, 'boss') and self.boss.body else None

        self._update_trapdoor_lifetimes(delta_time)

        for td in self._trapdoors:
            if td['active']:
                td['active_timer'] -= delta_time
                if td['active_timer'] <= 0:
                    td['active'] = False
                continue  # don't trigger again while cooling down

            td_left_m  = px2m(td['rect'].left)
            td_right_m = px2m(td['rect'].right)
            triggered  = False

            # Player
            if (player_body
                    and td_left_m <= player_body.position.x <= td_right_m
                    and self.jugador.on_ground):
                self._launch_player_up(player_body)
                triggered = True

            # Boss (Jenny) — ball is intentionally excluded
            if (boss_body
                    and td_left_m <= boss_body.position.x <= td_right_m
                    and self.boss.on_ground):
                self._launch_player_up(boss_body)
                triggered = True

            if triggered:
                td['active'] = True
                td['active_timer'] = TRAPDOOR_ACTIVE_MS

    def _launch_player_up(self, body):
        vel = body.linearVelocity
        body.linearVelocity = (vel.x, TRAPDOOR_LAUNCH_VY)

    # ─── JENNY AI ────────────────────────────────────────────

    def _update_jenny_ai(self, delta_time):
        if not (hasattr(self, 'boss') and self.boss.body and self.pelota.body and self.jugador.body):
            return

        if hasattr(self.boss, 'update_logic'):
            self.boss.update_logic(delta_time)

        if hasattr(self.boss, 'should_flash') and self.boss.should_flash():
            self.boss.trigger_flash()
            self._trigger_player_flash()

        goal_x_right = SW / PPM
        self.boss.update_fsm(
            ball_pos     = self.pelota.body.position,
            player_pos   = self.jugador.body.position,
            goal_x_right = goal_x_right,
        )

    def _trigger_player_flash(self):
        if not (self.boss.body and self.jugador.body):
            return

        if not self.boss.can_reach_player(self.jugador.body.position):
            return

        self._flash_overlay_alpha = FLASH_OVERLAY_ALPHA
        self._flash_hold_timer = FLASH_HOLD_BEFORE_FADE_MS

        if self.player_has_powerup:
            self._flash_protected_timer = 1500
            return

        if self.player_flashed:
            return

        self.player_flashed   = True
        self.flash_stun_timer = FLASH_STUN_DURATION

        if self.jugador.body:
            vel = self.jugador.body.linearVelocity
            self.jugador.body.linearVelocity = (vel.x * 0.2, vel.y)
        self.move_left_flag  = False
        self.move_right_flag = False

    def _update_flash_stun(self, delta_time):
        if self.player_flashed:
            self.flash_stun_timer -= delta_time
            if self.jugador.body:
                vel = self.jugador.body.linearVelocity
                self.jugador.body.linearVelocity = (vel.x * 0.88, vel.y)
            if self.flash_stun_timer <= 0:
                self.player_flashed   = False
                self.flash_stun_timer = 0

        if self._flash_hold_timer > 0:
            self._flash_hold_timer -= delta_time
            self._flash_overlay_alpha = FLASH_OVERLAY_ALPHA
            if self._flash_hold_timer < 0:
                self._flash_hold_timer = 0
        elif self._flash_overlay_alpha > 0:
            self._flash_overlay_alpha = max(0, self._flash_overlay_alpha - delta_time * 0.38)

        if hasattr(self, '_flash_protected_timer') and self._flash_protected_timer > 0:
            self._flash_protected_timer -= delta_time

        if self._sunglasses_timer > 0:
            self._sunglasses_timer -= delta_time
            if self._sunglasses_timer <= 0:
                self._sunglasses_timer = 0
                self.player_has_powerup = False

    def _on_powerup_collected(self):
        self._sunglasses_timer = SUNGLASSES_DURATION

    def _on_powerup_activate(self):
        pass

    def events(self, event_list):
        if self.player_flashed:
            from pygame.locals import KEYDOWN, K_ESCAPE
            from ingame_menu_scene import IngameMenu
            for ev in event_list:
                if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.director.apilarEscena(IngameMenu(self.director))
            return
        super().events(event_list)

    # ─── BOUNDARIES & GOALS ──────────────────────────────────

    def _create_boundaries(self):
        RocketFactory.create_boundaries(self.world, SW, GROUND_Y, GOAL_TOP_Y)

    def _create_goals(self):
        return RocketFactory.create_goals(
            self.world, SW, GROUND_Y, GOAL_W, GOAL_H, GOAL_POST, GOAL_TOP_Y
        )

    def _reset_positions(self):
        super()._reset_positions()

        if hasattr(self, 'boss') and self.boss.body:
            self.boss.body.position        = (px2m(JENNY_START[0]), px2m(JENNY_START[1]))
            self.boss.body.linearVelocity  = (0, 0)
            self.boss.body.angularVelocity = 0
            if hasattr(self.boss, '_flash_timer'):
                self.boss._flash_timer = int(self.boss.FLASH_INTERVAL * 0.6)

        self.player_flashed       = False
        self.flash_stun_timer     = 0
        self._flash_overlay_alpha = 0
        self._flash_hold_timer    = 0
        self._flash_protected_timer = 0
        self._sunglasses_timer    = 0
        self.player_has_powerup   = False

        self._destroy_trapdoors()
        self._spawn_timer = random.randint(1000, 2000)
        self._spawn_trapdoor()

    def update(self, delta_time):
        super().update(delta_time)

        self._update_jenny_ai(delta_time)
        self._update_trapdoors(delta_time)
        self._update_flash_stun(delta_time)

    # ─── RENDER ──────────────────────────────────────────────

    def _render_field(self, screen):
        try:
            if not hasattr(self, '_stadium_bg'):
                bg = pygame.image.load('./assets/stadiums/stadium1_bg.png').convert()
                self._stadium_bg = pygame.transform.scale(bg, (SW, SH))
            screen.blit(self._stadium_bg, (0, 0))
        except Exception:
            screen.fill((20, 80, 40))

        for td in self._trapdoors:
            color = TRAPDOOR_ACTIVE_COLOR if td['active'] else TRAPDOOR_COLOR
            pygame.draw.rect(screen, color, td['rect'])
            pygame.draw.rect(screen, TRAPDOOR_BORDER_COLOR, td['rect'], 2)
            mx = td['rect'].centerx
            y0 = td['rect'].top + 2
            y1 = td['rect'].bottom - 2
            pygame.draw.line(screen, TRAPDOOR_BORDER_COLOR, (mx - 15, y0), (mx - 15, y1), 1)
            pygame.draw.line(screen, TRAPDOOR_BORDER_COLOR, (mx + 15, y0), (mx + 15, y1), 1)
            pygame.draw.rect(screen, (120, 120, 160),
                             pygame.Rect(mx - 4, td['rect'].centery - 2, 8, 4))

    def _render_field_fg(self, screen):
        try:
            if not hasattr(self, '_goalpost_fg'):
                img = pygame.image.load('./assets/stadiums/excavator_shovel_goalpost_fg.png').convert_alpha()
                scaled = pygame.transform.scale(img, (GOAL_W, GOAL_H))
                self._goalpost_fg_l = scaled
                self._goalpost_fg_r = pygame.transform.flip(scaled, True, False)
            screen.blit(self._goalpost_fg_l, (0, GOAL_TOP_Y))
            screen.blit(self._goalpost_fg_r, (SW - GOAL_W, GOAL_TOP_Y))
        except Exception:
            pass

    def render(self, screen):
        super().render(screen)
        if self._flash_overlay_alpha > 0:
            self._draw_flash_overlay(screen)

        if self.player_flashed:
            self._draw_blind_indicator(screen)
        elif hasattr(self, '_flash_protected_timer') and self._flash_protected_timer > 0:
            self._draw_protected_indicator(screen)

        self._draw_jenny_indicator(screen)

    def _render_powerup_hud(self, screen):
        if self.player_has_powerup:
            secs_left = max(0, math.ceil(self._sunglasses_timer / 1000))
            label = f" GAFAS  {secs_left}s"
            if secs_left <= 1 and (pygame.time.get_ticks() // 300) % 2 == 0:
                color = (255, 80, 80)
            else:
                color = SUNGLASSES_HUD_COLOR
            text = pygame.font.SysFont('Arial', 16, bold=True).render(label, True, color)
            rect = text.get_rect(bottomleft=(10, SH - 10))
            bg = pygame.Surface((rect.width + 12, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            screen.blit(bg, (rect.x - 6, rect.y - 4))
            screen.blit(text, rect)

    def _draw_flash_overlay(self, screen):
        alpha = int(self._flash_overlay_alpha)
        if alpha <= 0:
            return
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((*FLASH_COLOR, alpha))
        screen.blit(overlay, (0, 0))

    def _draw_blind_indicator(self, screen):
        if not self.jugador.body:
            return

        blind_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        blind_surf.fill((255, 255, 200, 100))
        screen.blit(blind_surf, (0, 0))

        blink = (pygame.time.get_ticks() // 280) % 2 == 0
        if blink:
            px = int(m2px(self.jugador.body.position.x))
            py = int(m2px(self.jugador.body.position.y)) - 45

            text = self.flash_font.render("¡CEGADO!", True, FLASH_STUN_TXT_COLOR)
            rect = text.get_rect(center=(px, py))
            shadow = self.flash_font.render("¡CEGADO!", True, (80, 60, 0))
            screen.blit(shadow, shadow.get_rect(center=(px + 2, py + 2)))
            screen.blit(text, rect)

            t = pygame.time.get_ticks() / 180.0
            for i in range(4):
                angle = t + i * (math.pi / 2)
                sx = px + int(22 * math.cos(angle))
                sy = py + 16 + int(9 * math.sin(angle))
                pygame.draw.circle(screen, (255, 220, 0), (sx, sy), 3)

        bar_w, bar_h = 54, 5
        px2 = int(m2px(self.jugador.body.position.x))
        py2 = int(m2px(self.jugador.body.position.y)) - 56
        ratio = self.flash_stun_timer / FLASH_STUN_DURATION
        pygame.draw.rect(screen, (80, 80, 80),
                         pygame.Rect(px2 - bar_w // 2, py2, bar_w, bar_h))
        pygame.draw.rect(screen, FLASH_STUN_TXT_COLOR,
                         pygame.Rect(px2 - bar_w // 2, py2, int(bar_w * ratio), bar_h))

    def _draw_protected_indicator(self, screen):
        blink = (pygame.time.get_ticks() // 220) % 2 == 0
        if blink:
            text = self.flash_font.render("¡FLASH BLOQUEADO!", True, SUNGLASSES_COLOR)
            rect = text.get_rect(center=(SW // 2, SH // 2 - 60))
            bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            screen.blit(bg, (rect.x - 8, rect.y - 4))
            screen.blit(text, rect)

    def _draw_jenny_indicator(self, screen):
        if not hasattr(self, 'boss'):
            return

        if getattr(self.boss, 'is_flashing', False):
            blink = (pygame.time.get_ticks() // 120) % 2 == 0
            color = (255, 255, 100) if blink else (200, 180, 0)
            text = self.jenny_font.render("⚡ JENNY: ¡FLASH!", True, color)
        else:
            text = self.jenny_font.render("Jenny: en movimiento", True, (180, 220, 255))

        rect = text.get_rect(topright=JENNY_INDICATOR_POS)
        bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        screen.blit(bg, (rect.x - 8, rect.y - 4))
        screen.blit(text, rect)

        if hasattr(self.boss, '_flash_timer') and not self.boss.is_flashing:
            bar_w  = rect.width + 16
            bar_h  = 4
            bx     = rect.x - 8
            by     = rect.bottom + 2
            ratio  = min(1.0, self.boss._flash_timer / self.boss.FLASH_INTERVAL)
            bar_color = (255, 200, 0) if ratio > 0.75 else (100, 200, 255)
            pygame.draw.rect(screen, (50, 50, 50), pygame.Rect(bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, bar_color, pygame.Rect(bx, by, int(bar_w * ratio), bar_h))