import pygame
import random
import Box2D
import math
from match_scene import MatchScene, px2m, m2px, SW, SH, PPM
from settings import ScreenSettings
from factory import RocketFactory

# Constantes visuales del escenario 1
GROUND_Y   = 520
GOAL_W     = 80
GOAL_H     = 140
GOAL_POST  = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H

BG_COLOR       = (30, 120, 60)
GROUND_COLOR   = (20, 100, 50)
GOAL_COLOR     = (255, 255, 255)
GOAL_NET_COLOR = (180, 180, 180, 80)

# Constantes de barro
MUD_COLOR      = (101, 67, 33)
MUD_COLOR_DARK = (80, 50, 20)
MUD_HEIGHT     = 20
MUD_FRICTION_FACTOR = 0.85
MUD_CAR_FRICTION    = 0.60
MUD_SPAWN_INTERVAL  = 6000
MUD_LIFETIME        = 8000
MUD_MIN_WIDTH       = 80
MUD_MAX_WIDTH       = 140
MUD_MARGIN          = 100
MUD_MAX_ACTIVE      = 3

# Boss Bulldozer
BOSS_START        = (SW - 200, GROUND_Y - 60)
BOSS_SPEED        = 6.0
BOSS_SPEED_ANGRY  = 9.0
BOSS_BLEND        = 0.18
BOSS_CHASE_MARGIN = 0.3

# IA del Bulldozer
AI_AGGRO_RANGE    = 25.0   # Distancia (m) a la que prioriza embestir al jugador
AI_BALL_PRIORITY  = 12.0   # Si la pelota está más cerca de su portería que esto, va a por ella
AI_GOAL_X_LEFT    = px2m(GOAL_W)         # Límite X de la portería izquierda (en m)
AI_GOAL_X_RIGHT   = px2m(SW - GOAL_W)    # Límite X de la portería derecha (en m)

# Stun
STUN_DURATION     = 3000   # ms que dura el aturdimiento
STUN_COLOR        = (255, 255, 0)
STUN_FONT_SIZE    = 20
ANGRY_INDICATOR_COLOR = (255, 50, 50)
ANGRY_INDICATOR_POS   = (SW - 10, 10)  # esquina superior derecha


# ─── CONTACT LISTENER ────────────────────────────────────────

class SceneContactListener(Box2D.b2ContactListener):
    """Listener Box2D que detecta:
       1. Qué bodies están pisando sensores de barro
       2. Colisiones entre el boss y el jugador (para stun)
    """

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        # Barro
        self.bodies_in_mud = set()
        self._contact_count = {}
        # Flag para procesar colisión boss-jugador FUERA del step
        self.boss_hit_player = False

    def _get_mud_and_other(self, contact):
        fA = contact.fixtureA
        fB = contact.fixtureB
        udA = fA.userData
        udB = fB.userData
        if isinstance(udA, dict) and udA.get('type') == 'mud':
            return fA, fB.body
        if isinstance(udB, dict) and udB.get('type') == 'mud':
            return fB, fA.body
        return None, None

    def _is_boss_player_collision(self, contact):
        """Devuelve True si la colisión es entre el boss y el jugador."""
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
        # Barro
        mud_fix, other_body = self._get_mud_and_other(contact)
        if mud_fix and other_body:
            body_id = id(other_body)
            self._contact_count[body_id] = self._contact_count.get(body_id, 0) + 1
            self.bodies_in_mud.add(other_body)
            return

        # Boss vs Jugador — solo marcar flag, NO llamar lógica de juego
        if self._is_boss_player_collision(contact):
            self.boss_hit_player = True

    def EndContact(self, contact):
        mud_fix, other_body = self._get_mud_and_other(contact)
        if mud_fix and other_body:
            body_id = id(other_body)
            count = self._contact_count.get(body_id, 0) - 1
            if count <= 0:
                self._contact_count.pop(body_id, None)
                self.bodies_in_mud.discard(other_body)
            else:
                self._contact_count[body_id] = count

    def is_in_mud(self, body):
        return body in self.bodies_in_mud


class FirstScene(MatchScene):
    """Escenario 1: Campo de fútbol clásico verde con Bulldozer."""

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

    def _init_extras(self):
        """Crea el Bulldozer, el contact listener y el sistema de barro dinámico."""
        # Contact listener unificado (barro + colisiones boss)
        self.contact_listener = SceneContactListener(self)
        self.world.contactListener = self.contact_listener

        # Boss
        self.boss = RocketFactory.create_element(
            "boss", self.world, BOSS_START, subtipo='bulldozer'
        )
        self.grupo_sprites.add(self.boss)

        # Barro dinámico
        self.mud_patches = []
        self.mud_spawn_timer = MUD_SPAWN_INTERVAL * 0.5
        self._mud_next_side = random.choice(['left', 'right'])

        # Stun del jugador
        self.player_stunned = False
        self.stun_timer = 0
        self.stun_font = pygame.font.SysFont('Arial', STUN_FONT_SIZE, bold=True)
        self.angry_font = pygame.font.SysFont('Arial', 18, bold=True)

        # Control de stun: solo un stun por episodio de enfado
        self._stun_used_this_anger = False
        self._boss_was_angry = False

    # ─── STUN ─────────────────────────────────────────────────

    def _on_boss_hit_player(self):
        """Llamado cuando el boss toca al jugador."""
        if not hasattr(self, 'boss'):
            return
        # Solo aplica stun si el boss está enfadado, el jugador no está ya stunned
        # y no se ha usado el stun en este episodio de enfado
        if self.boss.is_angry and not self.player_stunned and not self._stun_used_this_anger:
            self.player_stunned = True
            self.stun_timer = STUN_DURATION
            self._stun_used_this_anger = True  # Consumir el stun de este episodio
            if self.jugador.body:
                self.jugador.body.linearVelocity = (0, self.jugador.body.linearVelocity.y)
            self.move_left_flag = False
            self.move_right_flag = False
            
            
    def _track_boss_anger(self):
        """Resetea el flag de stun cuando el boss pasa de calmado a enfadado."""
        if not hasattr(self, 'boss'):
            return
        currently_angry = self.boss.is_angry
        # Si el boss acaba de calmarse, preparar el stun para el próximo enfado
        if self._boss_was_angry and not currently_angry:
            self._stun_used_this_anger = False
        self._boss_was_angry = currently_angry
            
            
    def _check_boss_player_proximity(self):
        """Detección manual de proximidad boss-jugador como respaldo
        por si Box2D no genera contacto (ej: movimiento por velocidad directa)."""
        if not hasattr(self, 'boss') or not self.boss.body or not self.jugador.body:
            return
        if not self.boss.is_angry or self.player_stunned or self._stun_used_this_anger:
            return

        boss_pos = self.boss.body.position
        player_pos = self.jugador.body.position

        dx = abs(boss_pos.x - player_pos.x)
        dy = abs(boss_pos.y - player_pos.y)

        # Umbral de proximidad en metros (~sumando las mitades de ambos bodies)
        threshold_x = 2.5  # metros
        threshold_y = 2.0  # metros

        if dx < threshold_x and dy < threshold_y:
            self._on_boss_hit_player()
            

    def _update_stun(self, delta_time):
        """Actualiza el timer de aturdimiento del jugador."""
        if self.player_stunned:
            self.stun_timer -= delta_time
            # Mantener al jugador frenado mientras esté stunned
            if self.jugador.body:
                vel = self.jugador.body.linearVelocity
                self.jugador.body.linearVelocity = (vel.x * 0.85, vel.y)
            if self.stun_timer <= 0:
                self.player_stunned = False
                self.stun_timer = 0

    # ─── OVERRIDE EVENTS (bloquear input si stunned) ─────────

    def events(self, event_list):
        """Bloquea el movimiento del jugador si está stunned."""
        if self.player_stunned:
            # Solo permitir ESC (pausa) y QUIT, ignorar movimiento
            from pygame.locals import KEYDOWN, K_ESCAPE
            from ingame_menu_scene import IngameMenu
            for ev in event_list:
                if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.director.apilarEscena(IngameMenu(self.director))
            return

        # Si no está stunned, comportamiento normal
        super().events(event_list)

    # ─── BOUNDARIES & GOALS ──────────────────────────────────

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

    # ─── BARRO DINÁMICO CON BOX2D ────────────────────────────

    def _create_mud_body(self, x_px, w_px):
        cx_m = px2m(x_px + w_px / 2)
        cy_m = px2m(GROUND_Y - MUD_HEIGHT / 2)
        hw_m = px2m(w_px / 2)
        hh_m = px2m(MUD_HEIGHT / 2)

        body = self.world.CreateStaticBody(position=(cx_m, cy_m))
        body.CreatePolygonFixture(
            box=(hw_m, hh_m),
            isSensor=True,
            userData={'type': 'mud'}
        )
        return body

    def _destroy_mud_body(self, body):
        if body:
            self.world.DestroyBody(body)

    def _spawn_mud_patch(self):
        if len(self.mud_patches) >= MUD_MAX_ACTIVE:
            return

        w = random.randint(MUD_MIN_WIDTH, MUD_MAX_WIDTH)
        half = SW // 2

        if self._mud_next_side == 'left':
            x = random.randint(MUD_MARGIN, half - w - MUD_MARGIN)
        else:
            x = random.randint(half + MUD_MARGIN, SW - MUD_MARGIN - w)

        x = max(MUD_MARGIN, min(x, SW - MUD_MARGIN - w))
        rect = pygame.Rect(x, GROUND_Y - MUD_HEIGHT, w, MUD_HEIGHT)
        body = self._create_mud_body(x, w)
        self.mud_patches.append({'rect': rect, 'timer': 0, 'body': body})
        self._mud_next_side = 'right' if self._mud_next_side == 'left' else 'left'

    def _update_mud(self, delta_time):
        self.mud_spawn_timer += delta_time
        if self.mud_spawn_timer >= MUD_SPAWN_INTERVAL:
            self.mud_spawn_timer = 0
            self._spawn_mud_patch()

        for patch in self.mud_patches:
            patch['timer'] += delta_time

        alive = []
        for p in self.mud_patches:
            if p['timer'] < MUD_LIFETIME:
                alive.append(p)
            else:
                self._destroy_mud_body(p['body'])
        self.mud_patches = alive

    def _body_in_mud(self, body):
        if body and hasattr(self, 'contact_listener'):
            return self.contact_listener.is_in_mud(body)
        return False

    def _apply_mud_friction(self):
        if hasattr(self, 'pelota') and self.pelota.body:
            if self._body_in_mud(self.pelota.body):
                vel = self.pelota.body.linearVelocity
                self.pelota.body.linearVelocity = (
                    vel.x * MUD_FRICTION_FACTOR, vel.y
                )

    def _apply_mud_to_car(self, sprite, friction_factor):
        if hasattr(sprite, 'body') and sprite.body:
            if self._body_in_mud(sprite.body):
                vel = sprite.body.linearVelocity
                sprite.body.linearVelocity = (
                    vel.x * friction_factor, vel.y
                )

    # ─── IA DEL BOSS ─────────────────────────────────────────

    def _update_boss_ai(self, delta_time):
        """IA del Bulldozer: orquesta las decisiones del boss."""
        if not hasattr(self, 'boss') or not self.boss.body or not self.pelota.body:
            return

        # Actualizar lógica interna (enfado)
        if hasattr(self.boss, 'update_logic'):
            self.boss.update_logic(delta_time)

        # Decidir objetivo
        target_x = self.boss.decide_movement(
            ball_pos=self.pelota.body.position,
            player_pos=self.jugador.body.position,
            goal_x_right=AI_GOAL_X_RIGHT,
            ai_aggro_range=AI_AGGRO_RANGE,
            ai_ball_priority=AI_BALL_PRIORITY,
            boss_speed=BOSS_SPEED,
            boss_speed_angry=BOSS_SPEED_ANGRY,
            boss_blend=BOSS_BLEND
        )

        # Aplicar movimiento
        self.boss.apply_movement(
            target_x=target_x,
            ball_pos=self.pelota.body.position,
            player_pos=self.jugador.body.position,
            boss_speed=BOSS_SPEED,
            boss_speed_angry=BOSS_SPEED_ANGRY,
            boss_blend=BOSS_BLEND,
            boss_chase_margin=BOSS_CHASE_MARGIN
        )

    # ─── RESET ────────────────────────────────────────────────

    def _reset_positions(self):
        super()._reset_positions()
        if hasattr(self, 'boss') and self.boss.body:
            self.boss.body.position        = (px2m(BOSS_START[0]), px2m(BOSS_START[1]))
            self.boss.body.linearVelocity  = (0, 0)
            self.boss.body.angularVelocity = 0

        if hasattr(self, 'mud_patches'):
            for p in self.mud_patches:
                self._destroy_mud_body(p['body'])
            self.mud_patches = []
            self.mud_spawn_timer = MUD_SPAWN_INTERVAL * 0.5

        # Limpiar stun tras gol
        self.player_stunned = False
        self.stun_timer = 0
        self._stun_used_this_anger = False
        self._boss_was_angry = False

    # ─── UPDATE ───────────────────────────────────────────────

    def update(self, delta_time):
        super().update(delta_time)  # Aquí ocurre world.Step

        # Procesar colisión boss-jugador DESPUÉS del step (via Box2D contact)
        if hasattr(self, 'contact_listener') and self.contact_listener.boss_hit_player:
            self.contact_listener.boss_hit_player = False
            self._on_boss_hit_player()

        # Rastrear cambios de estado de enfado del boss
        self._track_boss_anger()

        # Detección manual de proximidad como respaldo
        self._check_boss_player_proximity()

        self._update_boss_ai(delta_time)
        self._update_mud(delta_time)
        self._apply_mud_friction()
        self._apply_mud_to_car(self.jugador, MUD_CAR_FRICTION)
        if hasattr(self, 'boss'):
            self._apply_mud_to_car(self.boss, MUD_CAR_FRICTION)
        self._update_stun(delta_time)

    # ─── RENDER ───────────────────────────────────────────────

    def _render_field(self, screen):
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SW, SH - GROUND_Y))

        pygame.draw.line(screen, (255, 255, 255), (SW // 2, 0), (SW // 2, GROUND_Y), 1)
        pygame.draw.circle(screen, (255, 255, 255), (SW // 2, GROUND_Y - 120), 60, 1)

        # Barro
        for patch in self.mud_patches:
            mud_rect = patch['rect']
            life_ratio = 1.0 - (patch['timer'] / MUD_LIFETIME)
            alpha = max(40, int(220 * life_ratio))

            mud_surf = pygame.Surface((mud_rect.width, mud_rect.height), pygame.SRCALPHA)
            mud_surf.fill((*MUD_COLOR, alpha))
            screen.blit(mud_surf, (mud_rect.x, mud_rect.y))

            border_surf = pygame.Surface((mud_rect.width, mud_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (*MUD_COLOR_DARK, alpha), (0, 0, mud_rect.width, mud_rect.height), 2)
            screen.blit(border_surf, (mud_rect.x, mud_rect.y))

            dec_surf = pygame.Surface((mud_rect.width, mud_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(dec_surf, (*MUD_COLOR_DARK, alpha),
                                (mud_rect.width // 2 - 15, mud_rect.height // 2 - 4, 30, 8))
            pygame.draw.ellipse(dec_surf, (*MUD_COLOR_DARK, alpha),
                                (10, mud_rect.height // 2 - 2, 20, 6))
            screen.blit(dec_surf, (mud_rect.x, mud_rect.y))

        self._draw_goal(screen, 'left')
        self._draw_goal(screen, 'right')

    def _draw_goal(self, screen, side):
        gx = 0 if side == 'left' else SW - GOAL_W

        net = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
        net.fill(GOAL_NET_COLOR)
        for i in range(0, GOAL_W, 10):
            pygame.draw.line(net, (200, 200, 200, 40), (i, 0), (i, GOAL_H), 1)
        for j in range(0, GOAL_H, 10):
            pygame.draw.line(net, (200, 200, 200, 40), (0, j), (GOAL_W, j), 1)
        screen.blit(net, (gx, GOAL_TOP_Y))

        pygame.draw.rect(screen, GOAL_COLOR,
                         (gx, GOAL_TOP_Y - GOAL_POST, GOAL_W, GOAL_POST))

        px = gx if side == 'left' else gx + GOAL_W - GOAL_POST
        pygame.draw.rect(screen, GOAL_COLOR,
                         (px, GOAL_TOP_Y - GOAL_POST, GOAL_POST, GOAL_H + GOAL_POST))

    def render(self, screen):
        """Override para añadir indicadores de stun y enfado del boss."""
        super().render(screen)
        if self.player_stunned:
            self._draw_stun_indicator(screen)
        self._draw_angry_indicator(screen)

    def _draw_stun_indicator(self, screen):
        """Dibuja un indicador visual de aturdimiento sobre el jugador."""
        if not self.jugador.body:
            return

        # Texto "STUNNED!" parpadeante
        blink = (pygame.time.get_ticks() // 300) % 2 == 0
        if blink:
            px = int(m2px(self.jugador.body.position.x))
            py = int(m2px(self.jugador.body.position.y)) - 40

            text = self.stun_font.render("STUNNED!", True, STUN_COLOR)
            rect = text.get_rect(center=(px, py))
            screen.blit(text, rect)

            # Estrellas giratorias alrededor del jugador
            t = pygame.time.get_ticks() / 200.0
            for i in range(3):
                angle = t + i * (2 * math.pi / 3)
                sx = px + int(20 * math.cos(angle))
                sy = py + 15 + int(8 * math.sin(angle))
                pygame.draw.circle(screen, STUN_COLOR, (sx, sy), 3)

        # Barra de tiempo restante de stun
        bar_w = 50
        bar_h = 5
        px = int(m2px(self.jugador.body.position.x))
        py = int(m2px(self.jugador.body.position.y)) - 50
        ratio = self.stun_timer / STUN_DURATION
        bg_rect = pygame.Rect(px - bar_w // 2, py, bar_w, bar_h)
        fg_rect = pygame.Rect(px - bar_w // 2, py, int(bar_w * ratio), bar_h)
        pygame.draw.rect(screen, (80, 80, 80), bg_rect)
        pygame.draw.rect(screen, STUN_COLOR, fg_rect)

    def _draw_angry_indicator(self, screen):
        """Muestra un indicador en la esquina superior derecha si el boss está enfadado."""
        if not hasattr(self, 'boss'):
            return

        if self.boss.is_angry:
            # Fondo rojo parpadeante
            blink = (pygame.time.get_ticks() // 400) % 2 == 0
            color = ANGRY_INDICATOR_COLOR if blink else (200, 30, 30)

            text = self.angry_font.render("⚠ BULLDOZER ENFADADO!", True, color)
            rect = text.get_rect(topright=ANGRY_INDICATOR_POS)

            # Fondo semitransparente
            bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            screen.blit(bg, (rect.x - 8, rect.y - 4))
            screen.blit(text, rect)
        else:
            text = self.angry_font.render("Bulldozer: calmado", True, (150, 255, 150))
            rect = text.get_rect(topright=ANGRY_INDICATOR_POS)

            bg = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 100))
            screen.blit(bg, (rect.x - 8, rect.y - 4))
            screen.blit(text, rect)