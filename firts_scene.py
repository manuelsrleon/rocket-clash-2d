import pygame
import random
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
MUD_FRICTION_FACTOR = 0.85       # Frenado de la pelota (más bajo = más freno)
MUD_CAR_FRICTION    = 0.60       # Frenado del coche/boss al empujar en barro
MUD_SPAWN_INTERVAL  = 6000       # ms entre apariciones de nuevas charcas
MUD_LIFETIME        = 8000       # ms que dura cada charca
MUD_MIN_WIDTH       = 80
MUD_MAX_WIDTH       = 140
MUD_MARGIN          = 100        # Margen desde los bordes para no tapar porterías
MUD_MAX_ACTIVE      = 3          # Máximo de charcas simultáneas

# Boss Bulldozer
BOSS_START       = (SW - 200, GROUND_Y - 60)
BOSS_SPEED       = 6.0
BOSS_BLEND       = 0.15
BOSS_CHASE_MARGIN = 0.5


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
        """Crea el Bulldozer y el sistema de barro dinámico."""
        self.boss = RocketFactory.create_element(
            "boss", self.world, BOSS_START, subtipo='bulldozer'
        )
        self.grupo_sprites.add(self.boss)

        # Sistema de barro dinámico: lista de {rect, timer}
        self.mud_patches = []
        self.mud_spawn_timer = MUD_SPAWN_INTERVAL * 0.5
        self._mud_next_side = random.choice(['left', 'right'])  # lado inicial aleatorio

    # ─── BOUNDARIES & GOALS ──────────────────────────────────

    def _create_boundaries(self):
        """Suelo, techo y paredes con hueco para porterías."""
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

    # ─── BARRO DINÁMICO ──────────────────────────────────────

    def _spawn_mud_patch(self):
        """Genera una nueva charca de barro alternando entre mitad izquierda y derecha."""
        if len(self.mud_patches) >= MUD_MAX_ACTIVE:
            return

        w = random.randint(MUD_MIN_WIDTH, MUD_MAX_WIDTH)
        half = SW // 2

        if self._mud_next_side == 'left':
            x = random.randint(MUD_MARGIN, half - w - MUD_MARGIN)
        else:
            x = random.randint(half + MUD_MARGIN, SW - MUD_MARGIN - w)

        # Asegurar que x es válido (por si los márgenes son muy grandes)
        x = max(MUD_MARGIN, min(x, SW - MUD_MARGIN - w))

        rect = pygame.Rect(x, GROUND_Y - MUD_HEIGHT, w, MUD_HEIGHT)
        self.mud_patches.append({'rect': rect, 'timer': 0})

        # Alternar lado para la próxima charca
        self._mud_next_side = 'right' if self._mud_next_side == 'left' else 'left'

    def _update_mud(self, delta_time):
        """Actualiza timers del barro: genera nuevas y elimina las caducadas."""
        self.mud_spawn_timer += delta_time
        if self.mud_spawn_timer >= MUD_SPAWN_INTERVAL:
            self.mud_spawn_timer = 0
            self._spawn_mud_patch()

        # Envejecer y eliminar
        for patch in self.mud_patches:
            patch['timer'] += delta_time
        self.mud_patches = [p for p in self.mud_patches if p['timer'] < MUD_LIFETIME]

    def _get_mud_rects(self):
        """Devuelve los pygame.Rect de cada zona de barro activa."""
        return [p['rect'] for p in self.mud_patches]

    def _sprite_in_mud(self, sprite):
        """Comprueba si un sprite está dentro de alguna zona de barro."""
        for mud_rect in self._get_mud_rects():
            if sprite.rect.colliderect(mud_rect):
                return True
        return False

    def _apply_mud_friction(self):
        """Aplica frenado extra a la pelota si está en barro."""
        if hasattr(self, 'pelota') and self.pelota.body:
            if self._sprite_in_mud(self.pelota):
                vel = self.pelota.body.linearVelocity
                self.pelota.body.linearVelocity = (
                    vel.x * MUD_FRICTION_FACTOR,
                    vel.y
                )

    def _apply_mud_to_car(self, sprite, friction_factor):
        """Aplica frenado extra a un coche/boss si está en barro."""
        if hasattr(sprite, 'body') and sprite.body:
            if self._sprite_in_mud(sprite):
                vel = sprite.body.linearVelocity
                sprite.body.linearVelocity = (
                    vel.x * friction_factor,
                    vel.y
                )

    # ─── IA DEL BOSS ─────────────────────────────────────────

    def _update_boss_ai(self, delta_time):
        """IA simple del Bulldozer: persigue la pelota horizontalmente."""
        if not hasattr(self, 'boss') or not self.boss.body or not self.pelota.body:
            return

        if hasattr(self.boss, 'update_logic'):
            self.boss.update_logic(delta_time)

        boss_x = self.boss.body.position.x
        ball_x = self.pelota.body.position.x

        speed = BOSS_SPEED
        if hasattr(self.boss, 'is_angry') and self.boss.is_angry:
            speed = BOSS_SPEED * 1.5

        diff = ball_x - boss_x
        vel = self.boss.body.linearVelocity

        if abs(diff) > BOSS_CHASE_MARGIN:
            target_vx = speed if diff > 0 else -speed
        else:
            target_vx = 0.0

        new_vx = vel.x + (target_vx - vel.x) * BOSS_BLEND
        self.boss.body.linearVelocity = (new_vx, vel.y)

        ball_y = self.pelota.body.position.y
        boss_y = self.boss.body.position.y
        if ball_y < boss_y - 3.0 and abs(diff) < 8.0:
            if hasattr(self.boss, 'on_ground') and self.boss.on_ground:
                self.boss.jump()

    # ─── RESET ────────────────────────────────────────────────

    def _reset_positions(self):
        """Resetea posiciones incluyendo al boss."""
        super()._reset_positions()
        if hasattr(self, 'boss') and self.boss.body:
            self.boss.body.position        = (px2m(BOSS_START[0]), px2m(BOSS_START[1]))
            self.boss.body.linearVelocity  = (0, 0)
            self.boss.body.angularVelocity = 0

    # ─── UPDATE ───────────────────────────────────────────────

    def update(self, delta_time):
        """Override para añadir IA del boss, barro dinámico y fricción."""
        super().update(delta_time)
        self._update_boss_ai(delta_time)
        self._update_mud(delta_time)
        self._apply_mud_friction()
        # Frenado al jugador y al boss si están en barro
        self._apply_mud_to_car(self.jugador, MUD_CAR_FRICTION)
        if hasattr(self, 'boss'):
            self._apply_mud_to_car(self.boss, MUD_CAR_FRICTION)

    # ─── RENDER ───────────────────────────────────────────────

    def _render_field(self, screen):
        """Campo verde clásico con decoración, barro dinámico y porterías."""
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SW, SH - GROUND_Y))

        # Línea central y círculo
        pygame.draw.line(screen, (255, 255, 255), (SW // 2, 0), (SW // 2, GROUND_Y), 1)
        pygame.draw.circle(screen, (255, 255, 255), (SW // 2, GROUND_Y - 120), 60, 1)

        # Zonas de barro activas (con efecto de fade según vida restante)
        for patch in self.mud_patches:
            mud_rect = patch['rect']
            life_ratio = 1.0 - (patch['timer'] / MUD_LIFETIME)
            alpha = max(40, int(220 * life_ratio))

            # Superficie con transparencia para fade-out
            mud_surf = pygame.Surface((mud_rect.width, mud_rect.height), pygame.SRCALPHA)
            mud_surf.fill((*MUD_COLOR, alpha))
            screen.blit(mud_surf, (mud_rect.x, mud_rect.y))

            # Borde oscuro
            border_surf = pygame.Surface((mud_rect.width, mud_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (*MUD_COLOR_DARK, alpha), (0, 0, mud_rect.width, mud_rect.height), 2)
            screen.blit(border_surf, (mud_rect.x, mud_rect.y))

            # Manchas decorativas
            cx = mud_rect.centerx
            cy = mud_rect.centery
            dec_surf = pygame.Surface((mud_rect.width, mud_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(dec_surf, (*MUD_COLOR_DARK, alpha),
                                (mud_rect.width // 2 - 15, mud_rect.height // 2 - 4, 30, 8))
            pygame.draw.ellipse(dec_surf, (*MUD_COLOR_DARK, alpha),
                                (10, mud_rect.height // 2 - 2, 20, 6))
            screen.blit(dec_surf, (mud_rect.x, mud_rect.y))

        # Porterías
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