import pygame
import random
import Box2D
import math
from match_scene import MatchScene, px2m, m2px, SW, SH, PPM
from settings import ScreenSettings
from factory import RocketFactory

# ─── CONSTANTES DEL ESCENARIO 2 ──────────────────────────────

GROUND_Y   = 520
GOAL_W     = 160
GOAL_H     = 320
GOAL_POST  = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H + 30

BG_COLOR       = (40, 40, 80)
GROUND_COLOR   = (30, 30, 60)
GOAL_COLOR     = (255, 255, 255)
GOAL_NET_COLOR = (180, 180, 180, 80)

# Boss MotoMoto
BOSS_START        = (SW - 200, GROUND_Y - 40)
BOSS_SPEED        = 7.0
BOSS_SPEED_ANGRY  = 12.0

# Stun (jugador recibe)
STUN_DURATION     = 2500   # MotoMoto aturde menos tiempo que Bulldozer
STUN_COLOR        = (255, 200, 0)
STUN_FONT_SIZE    = 20

# Indicadores
ANGRY_INDICATOR_COLOR = (255, 80, 30)
ANGRY_INDICATOR_POS   = (SW - 10, 10)

# Teletransporte visual
TELEPORT_FLASH_DURATION = 500  # ms del destello visual tras TP
TELEPORT_COLOR          = (0, 255, 255)

# Stun al boss (power-up)
BOSS_STUN_DURATION  = 4000
BOSS_STUN_COLOR     = (0, 200, 255)
POWERUP_READY_COLOR = (0, 255, 200)


# ─── CONTACT LISTENER ────────────────────────────────────────

class Scene2ContactListener(Box2D.b2ContactListener):
    """Listener Box2D para el escenario 2: colisiones boss-jugador."""

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.boss_hit_player = False

    def _is_boss_player_collision(self, contact):
        scene = self.scene
        if not hasattr(scene, 'boss') or not scene.boss.body:
            return False
        if not scene.jugador.body:
            return False

        bodyA = contact.fixtureA.body
        bodyB = contact.fixtureB.body
        boss_body = scene.boss.body
        player_body = scene.jugador.body

        if (bodyA is boss_body and bodyB is player_body):
            return True
        if (bodyA is player_body and bodyB is boss_body):
            return True
        return False

    def BeginContact(self, contact):
        if self._is_boss_player_collision(contact):
            self.boss_hit_player = True

    def EndContact(self, contact):
        pass


# ─── SECOND SCENE ────────────────────────────────────────────

class SecondScene(MatchScene):
    """Escenario 2: MotoMoto, un boss pequeño y rápido que se teletransporta."""

    def _get_config(self):
        return {
            'ground_y':     GROUND_Y,
            'player_start': (200, GROUND_Y - 60),
            'ball_start':   (SW // 2, GROUND_Y - 220),
            'gravity':      (0, 35),
            'player_speed': 12.0,
            'player_jump':  -28.0,
            'ground_blend': 0.35,
            'air_blend':    0.12,
            'player_hh':    3.5,
            'goal_pause_ms': 2000,
        }

    # ─── INIT EXTRAS ─────────────────────────────────────────

    def _init_extras(self):
        """Crea a MotoMoto y el contact listener."""
        # Contact listener
        self.contact_listener = Scene2ContactListener(self)
        self.world.contactListener = self.contact_listener

        # Boss
        self.boss = RocketFactory.create_element(
            "boss", self.world, BOSS_START, subtipo='motomoto'
        )
        self.grupo_sprites.add(self.boss)

        # Stun del jugador (recibido del boss)
        self.player_stunned = False
        self.stun_timer = 0
        self.stun_font = pygame.font.SysFont('Arial', STUN_FONT_SIZE, bold=True)
        self.angry_font = pygame.font.SysFont('Arial', 18, bold=True)

        # Control de stun: solo un stun por episodio de enfado
        self._stun_used_this_anger = False
        self._boss_was_angry = False

        # Stun al boss (power-up)
        self.boss_stunned = False
        self.boss_stun_timer = 0
        self.boss_stun_font = pygame.font.SysFont('Arial', STUN_FONT_SIZE, bold=True)

        # Efecto visual de teletransporte
        self.teleport_flash_timer = 0
        self.teleport_flash_pos = None  # posición (px) del destello

    # ─── STUN AL JUGADOR ─────────────────────────────────────

    def _on_boss_hit_player(self):
        """Llamado cuando el boss toca al jugador."""
        if not hasattr(self, 'boss'):
            return
        if self.boss_stunned:
            return
        if self.boss.is_angry and not self.player_stunned and not self._stun_used_this_anger:
            self.player_stunned = True
            self.stun_timer = STUN_DURATION
            self._stun_used_this_anger = True
            if self.jugador.body:
                self.jugador.body.linearVelocity = (0, self.jugador.body.linearVelocity.y)
            self.move_left_flag = False
            self.move_right_flag = False

    def _track_boss_anger(self):
        """Resetea el flag de stun cuando el boss pasa de calmado a enfadado."""
        if not hasattr(self, 'boss'):
            return
        currently_angry = self.boss.is_angry
        if self._boss_was_angry and not currently_angry:
            self._stun_used_this_anger = False
        self._boss_was_angry = currently_angry

    def _check_boss_player_proximity(self):
        """Detección manual de proximidad boss-jugador como respaldo."""
        if not hasattr(self, 'boss') or not self.boss.body or not self.jugador.body:
            return
        if not self.boss.is_angry or self.player_stunned or self._stun_used_this_anger:
            return
        if self.boss_stunned:
            return

        boss_pos = self.boss.body.position
        player_pos = self.jugador.body.position

        dx = abs(boss_pos.x - player_pos.x)
        dy = abs(boss_pos.y - player_pos.y)

        # MotoMoto es más pequeño, umbrales menores
        threshold_x = 2.0
        threshold_y = 1.5

        if dx < threshold_x and dy < threshold_y:
            self._on_boss_hit_player()

    def _update_stun(self, delta_time):
        """Actualiza el timer de aturdimiento del jugador."""
        if self.player_stunned:
            self.stun_timer -= delta_time
            if self.jugador.body:
                vel = self.jugador.body.linearVelocity
                self.jugador.body.linearVelocity = (vel.x * 0.85, vel.y)
            if self.stun_timer <= 0:
                self.player_stunned = False
                self.stun_timer = 0

    # ─── POWER-UP: STUN AL BOSS ──────────────────────────────

    def _on_powerup_collected(self):
        """Se llama cuando el jugador recoge la caja de power-up."""
        pass  # player_has_powerup ya se pone a True en MatchScene

    def _on_powerup_activate(self):
        """El jugador pulsa E para activar el power-up: stun al boss."""
        if not self.player_has_powerup:
            return
        if self.boss_stunned:
            return
        if not hasattr(self, 'boss') or not self.boss.body:
            return

        player_pos = self.jugador.body.position
        boss_pos = self.boss.body.position
        dx = abs(player_pos.x - boss_pos.x)
        dy = abs(player_pos.y - boss_pos.y)

        activate_range_x = 4.0
        activate_range_y = 3.0

        if dx < activate_range_x and dy < activate_range_y:
            self.boss_stunned = True
            self.boss_stun_timer = BOSS_STUN_DURATION
            self.player_has_powerup = False

            if self.boss.body:
                self.boss.body.linearVelocity = (0, self.boss.body.linearVelocity.y)

    def _update_boss_stun(self, delta_time):
        """Actualiza el stun aplicado al boss por el power-up."""
        if self.boss_stunned:
            self.boss_stun_timer -= delta_time
            if self.boss.body:
                vel = self.boss.body.linearVelocity
                self.boss.body.linearVelocity = (vel.x * 0.85, vel.y)
            if self.boss_stun_timer <= 0:
                self.boss_stunned = False
                self.boss_stun_timer = 0

    # ─── OVERRIDE EVENTS (bloquear input si stunned) ─────────

    def events(self, event_list):
        """Bloquea el movimiento del jugador si está stunned."""
        if self.player_stunned:
            from pygame.locals import KEYDOWN, K_ESCAPE, K_e
            from ingame_menu_scene import IngameMenu
            for ev in event_list:
                if ev.type == KEYDOWN:
                    if ev.key == K_ESCAPE:
                        self.director.apilarEscena(IngameMenu(self.director))
            return

        super().events(event_list)

    # ─── BOUNDARIES & GOALS (idénticas a FirstScene) ─────────

    def _create_boundaries(self):
        w = self.world
        g = w.CreateStaticBody(position=(px2m(SW / 2), px2m(GROUND_Y)))
        g.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.6)

        c = w.CreateStaticBody(position=(px2m(SW / 2), px2m(-5)))
        c.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.2)

        wl = w.CreateStaticBody(position=(px2m(-5), px2m(GOAL_TOP_Y / 2)))
        wl.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

        wr = w.CreateStaticBody(position=(px2m(SW + 5), px2m(GOAL_TOP_Y / 2)))
        wr.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

    def _create_goals(self):
        return (self._make_goal('left'), self._make_goal('right'))

    def _make_goal(self, side):
        gx = 0 if side == 'left' else SW - GOAL_W
        cx = px2m(gx + GOAL_W / 2)

        bar = self.world.CreateStaticBody(
            position=(cx, px2m(GOAL_TOP_Y - GOAL_POST / 2))
        )
        bar.CreatePolygonFixture(
            box=(px2m(GOAL_W / 2), px2m(GOAL_POST / 2)),
            friction=0.3, restitution=0.4
        )

        px_post = (gx - GOAL_POST / 2) if side == 'left' else (gx + GOAL_W + GOAL_POST / 2)
        back = self.world.CreateStaticBody(
            position=(px2m(px_post), px2m(GOAL_TOP_Y + GOAL_H / 2))
        )
        back.CreatePolygonFixture(
            box=(px2m(GOAL_POST / 2), px2m(GOAL_H / 2)),
            friction=0.3, restitution=0.4
        )

        floor = self.world.CreateStaticBody(position=(cx, px2m(GROUND_Y)))
        floor.CreatePolygonFixture(box=(px2m(GOAL_W / 2), px2m(5)), friction=0.6)

        return pygame.Rect(gx, GOAL_TOP_Y, GOAL_W, GOAL_H)

    # ─── IA DEL BOSS ─────────────────────────────────────────

    def _update_boss_ai(self, delta_time):
        """Actualiza la IA de MotoMoto: FSM + teletransporte."""
        if not (hasattr(self, 'boss') and self.boss.body
                and self.pelota.body and self.jugador.body):
            return

        # Si el boss está stunneado, no actúa
        if self.boss_stunned:
            return

        # 1. Reloj interno (enfado)
        if hasattr(self.boss, 'update_logic'):
            self.boss.update_logic(delta_time)

        # 2. Intentar teletransporte a la portería derecha (su portería)
        goal_x_right_m = px2m(SW - GOAL_W / 2)
        goal_y_m = px2m(GROUND_Y - 40)

        if hasattr(self.boss, 'try_teleport_to_goal'):
            teleported = self.boss.try_teleport_to_goal(
                self.pelota.body.position,
                goal_x_right_m,
                goal_y_m
            )
            if teleported:
                # Registrar efecto visual
                self.teleport_flash_timer = TELEPORT_FLASH_DURATION
                self.teleport_flash_pos = (
                    int(m2px(self.boss.body.position.x)),
                    int(m2px(self.boss.body.position.y))
                )

        # 3. FSM normal
        goal_x_right = SW / PPM
        self.boss.update_fsm(
            ball_pos=self.pelota.body.position,
            player_pos=self.jugador.body.position,
            goal_x_right=goal_x_right
        )

    # ─── RESET ────────────────────────────────────────────────

    def _reset_positions(self):
        super()._reset_positions()
        if hasattr(self, 'boss') and self.boss.body:
            self.boss.body.position = (px2m(BOSS_START[0]), px2m(BOSS_START[1]))
            self.boss.body.linearVelocity = (0, 0)
            self.boss.body.angularVelocity = 0

        # Limpiar stun del jugador
        self.player_stunned = False
        self.stun_timer = 0
        self._stun_used_this_anger = False
        self._boss_was_angry = False

        # Limpiar stun del boss
        self.boss_stunned = False
        self.boss_stun_timer = 0

        # Limpiar efecto de teletransporte
        self.teleport_flash_timer = 0
        self.teleport_flash_pos = None

    # ─── UPDATE ───────────────────────────────────────────────

    def update(self, delta_time):
        super().update(delta_time)

        # Procesar colisión boss-jugador DESPUÉS del step
        if hasattr(self, 'contact_listener') and self.contact_listener.boss_hit_player:
            self.contact_listener.boss_hit_player = False
            self._on_boss_hit_player()

        # Rastrear cambios de estado de enfado
        self._track_boss_anger()

        # Detección manual de proximidad como respaldo
        self._check_boss_player_proximity()

        self._update_boss_ai(delta_time)
        self._update_stun(delta_time)
        self._update_boss_stun(delta_time)

        # Timer de efecto visual de teletransporte
        if self.teleport_flash_timer > 0:
            self.teleport_flash_timer -= delta_time
            if self.teleport_flash_timer < 0:
                self.teleport_flash_timer = 0

    # ─── RENDER ───────────────────────────────────────────────

    def _render_field(self, screen):
        if not hasattr(self, '_stadium_bg'):
            bg = pygame.image.load('./assets/stadiums/stadium2_bg.png').convert()
            self._stadium_bg = pygame.transform.scale(bg, (SW, SH))
        screen.blit(self._stadium_bg, (0, 0))

        # Porterías fondo (reutiliza los mismos assets o dibuja rectángulos)
        if not hasattr(self, '_goalpost_bg'):
            try:
                img = pygame.image.load('./assets/stadiums/excavator_shovel_goalpost_bg.png').convert_alpha()
                scaled = pygame.transform.scale(img, (GOAL_W, GOAL_H))
                self._goalpost_bg_l = scaled
                self._goalpost_bg_r = pygame.transform.flip(scaled, True, False)
            except Exception:
                # Fallback: rectángulos simples
                self._goalpost_bg_l = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
                pygame.draw.rect(self._goalpost_bg_l, (*GOAL_NET_COLOR,), (0, 0, GOAL_W, GOAL_H))
                self._goalpost_bg_r = self._goalpost_bg_l.copy()
            self._goalpost_bg = True

        screen.blit(self._goalpost_bg_l, (0, GOAL_TOP_Y))
        screen.blit(self._goalpost_bg_r, (SW - GOAL_W, GOAL_TOP_Y))

    def _render_field_fg(self, screen):
        if not hasattr(self, '_goalpost_fg'):
            try:
                img = pygame.image.load('./assets/stadiums/excavator_shovel_goalpost_fg.png').convert_alpha()
                scaled = pygame.transform.scale(img, (GOAL_W, GOAL_H))
                self._goalpost_fg_l = scaled
                self._goalpost_fg_r = pygame.transform.flip(scaled, True, False)
            except Exception:
                self._goalpost_fg_l = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
                self._goalpost_fg_r = self._goalpost_fg_l.copy()
            self._goalpost_fg = True

        screen.blit(self._goalpost_fg_l, (0, GOAL_TOP_Y))
        screen.blit(self._goalpost_fg_r, (SW - GOAL_W, GOAL_TOP_Y))

    def render(self, screen):
        """Override para añadir indicadores visuales."""
        super().render(screen)
        if self.player_stunned:
            self._draw_stun_indicator(screen)
        if self.boss_stunned:
            self._draw_boss_stun_indicator(screen)
        self._draw_angry_indicator(screen)
        self._draw_teleport_flash(screen)

    # ─── INDICADORES VISUALES ─────────────────────────────────

    def _draw_stun_indicator(self, screen):
        """Dibuja un indicador visual de aturdimiento sobre el jugador."""
        if not self.jugador.body:
            return

        blink = (pygame.time.get_ticks() // 300) % 2 == 0
        if blink:
            px = int(m2px(self.jugador.body.position.x))
            py = int(m2px(self.jugador.body.position.y)) - 40

            text = self.stun_font.render("STUNNED!", True, STUN_COLOR)
            rect = text.get_rect(center=(px, py))
            screen.blit(text, rect)

            t = pygame.time.get_ticks() / 200.0
            for i in range(3):
                angle = t + i * (2 * math.pi / 3)
                sx = px + int(20 * math.cos(angle))
                sy = py + 15 + int(8 * math.sin(angle))
                pygame.draw.circle(screen, STUN_COLOR, (sx, sy), 3)

        bar_w = 50
        bar_h = 5
        px = int(m2px(self.jugador.body.position.x))
        py = int(m2px(self.jugador.body.position.y)) - 50
        ratio = self.stun_timer / STUN_DURATION
        bg_rect = pygame.Rect(px - bar_w // 2, py, bar_w, bar_h)
        fg_rect = pygame.Rect(px - bar_w // 2, py, int(bar_w * max(0, ratio)), bar_h)
        pygame.draw.rect(screen, (80, 80, 80), bg_rect)
        pygame.draw.rect(screen, STUN_COLOR, fg_rect)

    def _draw_boss_stun_indicator(self, screen):
        """Dibuja un indicador visual de aturdimiento sobre el boss."""
        if not hasattr(self, 'boss') or not self.boss.body:
            return

        bx = int(m2px(self.boss.body.position.x))
        by = int(m2px(self.boss.body.position.y)) - 35

        blink = (pygame.time.get_ticks() // 250) % 2 == 0
        if blink:
            text = self.boss_stun_font.render("STUNNED!", True, BOSS_STUN_COLOR)
            rect = text.get_rect(center=(bx, by))
            screen.blit(text, rect)

            t = pygame.time.get_ticks() / 180.0
            for i in range(4):
                angle = t + i * (2 * math.pi / 4)
                sx = bx + int(25 * math.cos(angle))
                sy = by + 15 + int(10 * math.sin(angle))
                pygame.draw.circle(screen, BOSS_STUN_COLOR, (sx, sy), 4)

        bar_w = 60
        bar_h = 6
        py = by - 15
        ratio = self.boss_stun_timer / BOSS_STUN_DURATION
        bg_rect = pygame.Rect(bx - bar_w // 2, py, bar_w, bar_h)
        fg_rect = pygame.Rect(bx - bar_w // 2, py, int(bar_w * max(0, ratio)), bar_h)
        pygame.draw.rect(screen, (80, 80, 80), bg_rect)
        pygame.draw.rect(screen, BOSS_STUN_COLOR, fg_rect)

    def _draw_angry_indicator(self, screen):
        """Muestra un indicador en la esquina superior derecha."""
        if not hasattr(self, 'boss'):
            return

        if self.boss_stunned:
            text = self.angry_font.render("⚡ MotoMoto STUNNED!", True, BOSS_STUN_COLOR)
            rect = text.get_rect(topright=ANGRY_INDICATOR_POS)
            bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            screen.blit(bg, (rect.x - 8, rect.y - 4))
            screen.blit(text, rect)
        elif self.boss.is_angry:
            blink = (pygame.time.get_ticks() // 400) % 2 == 0
            color = ANGRY_INDICATOR_COLOR if blink else (200, 60, 30)

            text = self.angry_font.render("⚠ MOTOMOTO ENFADADO!", True, color)
            rect = text.get_rect(topright=ANGRY_INDICATOR_POS)

            bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            screen.blit(bg, (rect.x - 8, rect.y - 4))
            screen.blit(text, rect)
        else:
            text = self.angry_font.render("MotoMoto: calmado", True, (150, 255, 150))
            rect = text.get_rect(topright=ANGRY_INDICATOR_POS)

            bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 100))
            screen.blit(bg, (rect.x - 8, rect.y - 4))
            screen.blit(text, rect)

    def _draw_teleport_flash(self, screen):
        """Dibuja un destello en la posición donde MotoMoto se teletransportó."""
        if self.teleport_flash_timer <= 0 or self.teleport_flash_pos is None:
            return

        alpha = int(255 * (self.teleport_flash_timer / TELEPORT_FLASH_DURATION))
        alpha = max(0, min(255, alpha))

        cx, cy = self.teleport_flash_pos
        radius = int(40 * (self.teleport_flash_timer / TELEPORT_FLASH_DURATION)) + 10

        # Círculo exterior
        flash_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(flash_surf, (*TELEPORT_COLOR, alpha // 2), (radius, radius), radius)
        # Círculo interior más brillante
        inner_r = max(4, radius // 2)
        pygame.draw.circle(flash_surf, (*TELEPORT_COLOR, alpha), (radius, radius), inner_r)

        screen.blit(flash_surf, (cx - radius, cy - radius))

        # Partículas de teletransporte
        t = pygame.time.get_ticks() / 150.0
        for i in range(6):
            angle = t + i * (2 * math.pi / 6)
            dist = radius * 0.8
            px = cx + int(dist * math.cos(angle))
            py = cy + int(dist * math.sin(angle))
            pygame.draw.circle(screen, TELEPORT_COLOR, (px, py), 3)