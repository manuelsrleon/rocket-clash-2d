import pygame
import math
import random
import Box2D
from match_scene import MatchScene, px2m, m2px, SW, SH, PPM
from factory import RocketFactory


GROUND_Y   = 570
LOGICAL_GOAL_X     = 10
LOGICAL_GOAL_W     = 140
LOGICAL_GOAL_H     = 170
LOGICAL_GOAL_POST  = GROUND_Y
LOGICAL_GOAL_TOP_Y = GROUND_Y-LOGICAL_GOAL_H
SKY = 0
GOAL_X = 10
# Scene constants
GOAL_W     = 150
GOAL_H     = 250
GOAL_POST  = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H + 30
L_GOAL_POS = -100
JENNY_START = (SW - 200, GROUND_Y - 60)
JENNY_INDICATOR_POS = (SW - 10, 10)

# Flash
FLASH_STUN_DURATION   = 2000   # ms
FLASH_COLOR           = (255, 255, 240)
FLASH_STUN_TXT_COLOR  = (255, 230, 0)
FLASH_FONT_SIZE       = 20
FLASH_OVERLAY_ALPHA   = 210
FLASH_HOLD_BEFORE_FADE_MS = 2000

# Sunglasses power-up duration in ms
SUNGLASSES_DURATION  = 10000
SUNGLASSES_COLOR     = (0, 200, 255)
SUNGLASSES_HUD_COLOR = (0, 220, 180)


# Trapdoors
TRAPDOOR_W            = 80     # px
TRAPDOOR_H            = 14     # px
TRAPDOOR_COLOR        = (50, 50, 70)
TRAPDOOR_BORDER_COLOR = (80, 80, 120)
TRAPDOOR_ACTIVE_COLOR = (255, 80, 0)
TRAPDOOR_LAUNCH_VY    = -37.0
TRAPDOOR_ACTIVE_MS    = 400
TRAPDOOR_VISIBLE_MS_RANGE = (2000, 5000)
TRAPDOOR_HIDDEN_MS_RANGE  = (15000, 25000)

TRAPDOOR_MAX_VISIBLE  = 2
TRAPDOOR_SPAWN_INTERVAL_RANGE = (4000, 9000)  # ms entre intentos de spawn
TRAPDOOR_X_MIN = GOAL_W + 40
TRAPDOOR_X_MAX = SW - GOAL_W - 40
TRAPDOOR_MIN_SEPARATION = 120  # px mínimo entre centros de trampillas


class ThirdSceneContactListener(Box2D.b2ContactListener):
    """Listener for ThirdScene: adds player-trapdoor contact detection."""

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self._trapdoor_contact_count = {}

    def reset_flags(self):
        self._trapdoor_contact_count = {}

    def clear_trapdoor_contacts(self, trapdoor_idx):
        keys_to_remove = [key for key in self._trapdoor_contact_count if key[0] == trapdoor_idx]
        for key in keys_to_remove:
            self._trapdoor_contact_count.pop(key, None)

    def _get_trapdoor_player_pair(self, contact):
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB
        data_a = fixture_a.userData
        data_b = fixture_b.userData

        player_body = self.scene.jugador.body if hasattr(self.scene, 'jugador') else None
        if player_body is None:
            return None, None

        if isinstance(data_a, dict) and data_a.get('type') == 'trapdoor' and fixture_b.body is player_body:
            return data_a.get('index'), player_body
        if isinstance(data_b, dict) and data_b.get('type') == 'trapdoor' and fixture_a.body is player_body:
            return data_b.get('index'), player_body
        return None, None

    def BeginContact(self, contact):
        trapdoor_idx, player_body = self._get_trapdoor_player_pair(contact)
        if trapdoor_idx is None or player_body is None:
            return

        key = (trapdoor_idx, id(player_body))
        count = self._trapdoor_contact_count.get(key, 0) + 1
        self._trapdoor_contact_count[key] = count

        if count == 1:
            td = self.scene._get_trapdoor_by_index(trapdoor_idx)
            if td is not None:
                td['player_inside'] = True

    def EndContact(self, contact):
        trapdoor_idx, player_body = self._get_trapdoor_player_pair(contact)
        if trapdoor_idx is None or player_body is None:
            return

        key = (trapdoor_idx, id(player_body))
        count = self._trapdoor_contact_count.get(key, 0) - 1
        if count <= 0:
            self._trapdoor_contact_count.pop(key, None)
            td = self.scene._get_trapdoor_by_index(trapdoor_idx)
            if td is not None:
                td['player_inside'] = False
        else:
            self._trapdoor_contact_count[key] = count

class ThirdScene(MatchScene):
    """
    Scene: La Jenny.
    Mechanics:
        - Jenny is faster than the player.
        - Every ~20s she launches a headlight flash that blinds the player for 2s (unless wearing sunglasses).
        - There are up to 2 trapdoors at random positions on the ground that launch the player upwards.
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
            'music_name': "match3_bg_playing_theme"
        }

    def _init_extras(self):
        self.contact_listener = ThirdSceneContactListener(self)
        self.world.contactListener = self.contact_listener

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

        # Trapdoors: lista dinámica + contador de índices únicos
        self._trapdoors = []
        self._next_trapdoor_index = 0
        self._spawn_timer = random.randint(*TRAPDOOR_SPAWN_INTERVAL_RANGE)

    def _get_trapdoor_by_index(self, index):
        """Busca una trampilla por su índice único."""
        for td in self._trapdoors:
            if td['index'] == index:
                return td
        return None

    def _random_x_center(self):
        """Genera una posición X aleatoria para una trampilla, respetando separación mínima."""
        for _ in range(30):
            cx = random.randint(TRAPDOOR_X_MIN, TRAPDOOR_X_MAX)
            too_close = False
            for td in self._trapdoors:
                if abs(td['rect'].centerx - cx) < TRAPDOOR_MIN_SEPARATION:
                    too_close = True
                    break
            if not too_close:
                return cx
        return None

    def _spawn_trapdoor(self):
        """Crea una trampilla en una posición aleatoria del suelo."""
        cx_px = self._random_x_center()
        if cx_px is None:
            return

        idx = self._next_trapdoor_index
        self._next_trapdoor_index += 1

        x_px = cx_px - TRAPDOOR_W // 2
        y_px = GROUND_Y - TRAPDOOR_H
        rect = pygame.Rect(x_px, y_px, TRAPDOOR_W, TRAPDOOR_H)

        sensor_body = RocketFactory.create_trapdoor_sensor(
            self.world, cx_px, y_px, TRAPDOOR_W, TRAPDOOR_H, idx
        )

        self._trapdoors.append({
            'index': idx,
            'rect': rect,
            'sensor_body': sensor_body,
            'player_inside': False,
            'active': False,
            'active_timer': 0,
            'lifetime': random.randint(*TRAPDOOR_VISIBLE_MS_RANGE),
        })

    def _despawn_trapdoor(self, td):
        """Elimina una trampilla y destruye su body."""
        body = td.get('sensor_body')
        if body:
            RocketFactory.destroy_body(self.world, body)
            td['sensor_body'] = None
        if hasattr(self, 'contact_listener'):
            self.contact_listener.clear_trapdoor_contacts(td['index'])
        self._trapdoors.remove(td)

    def _destroy_trapdoors(self):
        for td in list(self._trapdoors):
            body = td.get('sensor_body')
            if body:
                RocketFactory.destroy_body(self.world, body)
                td['sensor_body'] = None
        self._trapdoors = []

    def _update_trapdoors(self, delta_time):
        player_body = self.jugador.body
        if not player_body:
            return

        # Reducir lifetime de cada trampilla y eliminar las expiradas
        for td in list(self._trapdoors):
            td['lifetime'] -= delta_time
            if td['lifetime'] <= 0 and not td['active']:
                self._despawn_trapdoor(td)

        # Intentar spawnear nuevas trampillas
        self._spawn_timer -= delta_time
        if self._spawn_timer <= 0:
            self._spawn_timer = random.randint(*TRAPDOOR_SPAWN_INTERVAL_RANGE)
            if len(self._trapdoors) < TRAPDOOR_MAX_VISIBLE:
                self._spawn_trapdoor()

        boss_body = self.boss.body if hasattr(self, 'boss') and self.boss.body else None

        for td in self._trapdoors:
            if td['active']:
                td['active_timer'] -= delta_time
                if td['active_timer'] <= 0:
                    td['active'] = False
                continue

            rect = td['rect']
            td_left_m  = px2m(rect.left)
            td_right_m = px2m(rect.right)

            launched = False

            player_cx_m = player_body.position.x
            if td_left_m <= player_cx_m <= td_right_m and self.jugador.on_ground:
                self._launch_player_up(player_body)
                launched = True

            if boss_body:
                boss_cx_m = boss_body.position.x
                if td_left_m <= boss_cx_m <= td_right_m and self.boss.on_ground:
                    self._launch_player_up(boss_body)
                    launched = True

            if launched:
                td['active'] = True
                td['active_timer'] = TRAPDOOR_ACTIVE_MS

    def _launch_player_up(self, body):
        vel = body.linearVelocity
        body.linearVelocity = (vel.x, TRAPDOOR_LAUNCH_VY)

    # Jenny AI logic
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
            ball_pos   = self.pelota.body.position,
            player_pos = self.jugador.body.position,
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

    # ─── BOUNDARIES & GOALS (delegado a RocketFactory) ───────

    def _create_boundaries(self):
        RocketFactory.create_boundaries(self.world, SW, GROUND_Y, GOAL_TOP_Y)

    def _create_goals(self):
        goal_w = GOAL_W
        goal_x = GOAL_X
        goal_h = GOAL_H
        goal_top_y = LOGICAL_GOAL_TOP_Y
        goal_post = GOAL_POST
        ground_y = GROUND_Y
        
        world = self.world
    
        side = 'left'
        gx = 0 if side == 'left' else screen_width - goal_w
        cx = px2m(gx + goal_w / 2)
        
        # Travesaño superior
        bar = world.CreateStaticBody(
            position=(0, px2m(LOGICAL_GOAL_TOP_Y-20)),
        )
        upper_hitbox = [
            (0,0),
            (px2m(LOGICAL_GOAL_W),0), 
            (px2m(0),px2m(-40)),
            #(px2m(20),px2m(SKY)),
            #(px2m(10),px2m(-100)),
            #(px2m(10),px2m(LOGICAL_GOAL_TOP_Y)),
            #(0,px2m(LOGICAL_GOAL_TOP_Y))
            ]
        bar.CreatePolygonFixture(
            vertices=upper_hitbox,
            friction=0.3, restitution=0.4
        )


        # Palo trasero
        back = world.CreateStaticBody(
            position=(px2m(LOGICAL_GOAL_X-10), px2m(GROUND_Y-10)),
        )
        back.CreatePolygonFixture(
            box=(px2m(6), px2m(LOGICAL_GOAL_H)),
            friction=0.3, restitution=0.4
        )

        
        bar.CreatePolygonFixture(
            vertices=upper_hitbox,
            friction=0.3, restitution=0.4
        )
        back.CreatePolygonFixture(
            box=(px2m(goal_post / 2), px2m(goal_h / 2)),
            friction=0.3, restitution=0.4
        )
        
        # LADO DERECHO

        side = 'right'
        gx = 0 if side == 'right' else screen_width - goal_w
        cx = px2m(gx + goal_w / 2)
        correction_offset = 0
        # Travesaño superior
        # Travesaño superior
       
        upper_hitbox_r = [
            (px2m(-LOGICAL_GOAL_W+correction_offset),0),
            (px2m(correction_offset),0), 
            (px2m(correction_offset),px2m(-40)),
            #(px2m(20),px2m(SKY)),
            #(px2m(10),px2m(-100)),
            #(px2m(10),px2m(LOGICAL_GOAL_TOP_Y)),
            #(0,px2m(LOGICAL_GOAL_TOP_Y))
            ]
        bar_r = world.CreateStaticBody(
            position=(px2m(SW), px2m(LOGICAL_GOAL_TOP_Y-20)),
        )
        bar_r.CreatePolygonFixture(
            vertices=upper_hitbox_r,
            friction=0.3, restitution=0.4
        )
        

        back_r = world.CreateStaticBody(
            position=(px2m(SW-LOGICAL_GOAL_X+10), px2m(GROUND_Y-40)),
        )

        back_r.CreatePolygonFixture(
            box=(px2m(goal_post / 2), px2m(goal_h / 2)),
            friction=0.3, restitution=0.4
        )
        #if self.PHYSICS_DEBUG_MODE:
            #pygame.draw.aaline(self.suface, (255,0,255), LOGICAL_GOAL_H, LOGICA)

        return pygame.Rect(LOGICAL_GOAL_X-80, LOGICAL_GOAL_TOP_Y, LOGICAL_GOAL_W, LOGICAL_GOAL_H), pygame.Rect(SW-LOGICAL_GOAL_W+LOGICAL_GOAL_X+80, LOGICAL_GOAL_TOP_Y, LOGICAL_GOAL_W, LOGICAL_GOAL_H)

    def _reset_positions(self):
        super()._reset_positions()

        if hasattr(self, 'boss') and self.boss.body:
            self.boss.body.position        = (px2m(JENNY_START[0]), px2m(JENNY_START[1]))
            self.boss.body.linearVelocity  = (0, 0)
            self.boss.body.angularVelocity = 0
            if hasattr(self.boss, '_flash_timer'):
                self.boss._flash_timer = int(self.boss.FLASH_INTERVAL * 0.6)

        self.player_flashed   = False
        self.flash_stun_timer = 0
        self._flash_overlay_alpha = 0
        self._flash_hold_timer = 0
        self._flash_protected_timer = 0
        self._sunglasses_timer = 0
        self.player_has_powerup = False

        if hasattr(self, 'contact_listener') and hasattr(self.contact_listener, 'reset_flags'):
            self.contact_listener.reset_flags()

        # Destruir trampillas existentes y reiniciar
        self._destroy_trapdoors()
        self._next_trapdoor_index = 0
        self._spawn_timer = random.randint(*TRAPDOOR_SPAWN_INTERVAL_RANGE)

    def update(self, delta_time):
        super().update(delta_time)

        self._update_jenny_ai(delta_time)
        self._update_trapdoors(delta_time)
        self._update_flash_stun(delta_time)

    def _render_field(self, screen):
        try:
            if not hasattr(self, '_stadium_bg'):
                bg = pygame.image.load('./assets/stadiums/stadium3_bg.png').convert()
                self._stadium_bg = pygame.transform.scale(bg, (SW, SH))
            screen.blit(self._stadium_bg, (0, 0))
        except Exception:
            screen.fill((20, 80, 40))

        # Trapdoors
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
        
        # Porterías fondo
        if not hasattr(self, '_goalpost_bg'):
            try:
                l_goalpost_bg    = pygame.image.load('./assets/stadiums/stadium-3-goalpost-bg.png').convert_alpha()
                r_goalpost_bg    = pygame.image.load('./assets/stadiums/stadium-3-goalpost-bg.png').convert_alpha()

                l_goalpost_bg_scaled = pygame.transform.scale(l_goalpost_bg, (GOAL_W*2, GOAL_H))
                r_goalpost_bg_scaled = pygame.transform.flip(l_goalpost_bg_scaled, True, False)
                
                self._goalpost_bg_l = l_goalpost_bg_scaled
                self._goalpost_bg_r = r_goalpost_bg_scaled
            except Exception:
                self._goalpost_bg_l = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
                pygame.draw.rect(self._goalpost_bg_l, (*GOAL_NET_COLOR,), (0, 0, GOAL_W, GOAL_H))
                self._goalpost_bg_r = self._goalpost_bg_l.copy()
            self._goalpost_bg = True

        screen.blit(self._goalpost_bg_l, (L_GOAL_POS, GOAL_TOP_Y))
        screen.blit(self._goalpost_bg_r, (SW - GOAL_W+L_GOAL_POS+50, GOAL_TOP_Y))

    def _render_field_fg(self, screen):
        if not hasattr(self, '_goalpost_fg'):
            try:
                l_goalpost_fg    = pygame.image.load('./assets/stadiums/stadium-3-goalpost-fg.png').convert_alpha()

                l_goalpost_fg_scaled = pygame.transform.scale(l_goalpost_fg, (GOAL_W*2, GOAL_H))
                r_goalpost_fg_scaled = pygame.transform.flip(l_goalpost_fg_scaled, True, False)

                self._goalpost_fg_l = l_goalpost_fg_scaled
                self._goalpost_fg_r = r_goalpost_fg_scaled
            except Exception:
                self._goalpost_fg_l = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
                self._goalpost_fg_r = self._goalpost_fg_l.copy()
            self._goalpost_fg = True

        screen.blit(self._goalpost_fg_l, (L_GOAL_POS, GOAL_TOP_Y))
        screen.blit(self._goalpost_fg_r, (SW - GOAL_W-50, GOAL_TOP_Y))

    def render(self, screen):
        super().render(screen)
        if self._flash_overlay_alpha > 0:
            self._draw_flash_overlay(screen)

        if self.player_flashed:
            self._draw_blind_indicator(screen)
        elif hasattr(self, '_flash_protected_timer') and self._flash_protected_timer > 0:
            self._draw_protected_indicator(screen)

        if not self.is_exiting:
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