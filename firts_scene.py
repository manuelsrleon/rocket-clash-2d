import pygame
from match_scene import MatchScene, px2m, m2px, SW, SH
from settings import ScreenSettings

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
MUD_FRICTION_FACTOR = 0.92  # Factor de frenado por frame (más bajo = más frenado)

# Zonas de barro: lista de (x, ancho) — posicionadas sobre el suelo
MUD_ZONES = [
    (SW - GOAL_W - 140, 120),  # Solo delante de la portería derecha
]


class FirstScene(MatchScene):
    """Escenario 1: Campo de fútbol clásico verde."""

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

    # ...existing code...

    def _create_boundaries(self):
        """Suelo, techo y paredes con hueco para porterías."""
        w = self.world

        # Suelo
        g = w.CreateStaticBody(position=(px2m(SW / 2), px2m(GROUND_Y)))
        g.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.6)

        # Techo
        c = w.CreateStaticBody(position=(px2m(SW / 2), px2m(-5)))
        c.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.2)

        # Paredes — solo por encima de las porterías
        wl = w.CreateStaticBody(position=(px2m(-5), px2m(GOAL_TOP_Y / 2)))
        wl.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

        wr = w.CreateStaticBody(position=(px2m(SW + 5), px2m(GOAL_TOP_Y / 2)))
        wr.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

    # ...existing code...

    def _create_goals(self):
        """Porterías con travesaño, poste trasero y suelo interior."""
        return (
            self._make_goal('left'),
            self._make_goal('right'),
        )

    def _make_goal(self, side):
        gx = 0 if side == 'left' else SW - GOAL_W
        cx = px2m(gx + GOAL_W / 2)

        # Travesaño
        bar = self.world.CreateStaticBody(
            position=(cx, px2m(GOAL_TOP_Y - GOAL_POST / 2))
        )
        bar.CreatePolygonFixture(
            box=(px2m(GOAL_W / 2), px2m(GOAL_POST / 2)),
            friction=0.3, restitution=0.4
        )

        # Poste trasero
        px_post = (gx - GOAL_POST / 2) if side == 'left' else (gx + GOAL_W + GOAL_POST / 2)
        back = self.world.CreateStaticBody(
            position=(px2m(px_post), px2m(GOAL_TOP_Y + GOAL_H / 2))
        )
        back.CreatePolygonFixture(
            box=(px2m(GOAL_POST / 2), px2m(GOAL_H / 2)),
            friction=0.3, restitution=0.4
        )

        # Suelo interior
        floor = self.world.CreateStaticBody(position=(cx, px2m(GROUND_Y)))
        floor.CreatePolygonFixture(
            box=(px2m(GOAL_W / 2), px2m(5)), friction=0.6
        )

        return pygame.Rect(gx, GOAL_TOP_Y, GOAL_W, GOAL_H)

    def _get_mud_rects(self):
        """Devuelve los pygame.Rect de cada zona de barro."""
        rects = []
        for (mx, mw) in MUD_ZONES:
            rects.append(pygame.Rect(mx, GROUND_Y - MUD_HEIGHT, mw, MUD_HEIGHT))
        return rects

    def _ball_in_mud(self, ball):
        """Comprueba si la pelota está dentro de alguna zona de barro."""
        ball_rect = ball.rect
        for mud_rect in self._get_mud_rects():
            if ball_rect.colliderect(mud_rect):
                return True
        return False

    def _apply_mud_friction(self):
        """Aplica frenado extra a la pelota si está en una zona de barro."""
        if hasattr(self, 'pelota') and self.pelota.body:
            if self._ball_in_mud(self.pelota):
                vel = self.pelota.body.linearVelocity
                self.pelota.body.linearVelocity = (
                    vel.x * MUD_FRICTION_FACTOR,
                    vel.y
                )

    def update(self, delta_time):
        """Override para añadir el efecto de barro."""
        super().update(delta_time)
        self._apply_mud_friction()

    def _render_field(self, screen):
        """Campo verde clásico con decoración y zonas de barro."""
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SW, SH - GROUND_Y))

        # Línea central y círculo
        pygame.draw.line(screen, (255, 255, 255), (SW // 2, 0), (SW // 2, GROUND_Y), 1)
        pygame.draw.circle(screen, (255, 255, 255), (SW // 2, GROUND_Y - 120), 60, 1)

        # Zonas de barro
        for mud_rect in self._get_mud_rects():
            # Capa base de barro
            pygame.draw.rect(screen, MUD_COLOR, mud_rect)
            # Borde oscuro para dar profundidad
            pygame.draw.rect(screen, MUD_COLOR_DARK, mud_rect, 2)
            # Manchas de barro decorativas
            cx = mud_rect.centerx
            cy = mud_rect.centery
            pygame.draw.ellipse(screen, MUD_COLOR_DARK,
                                (cx - 15, cy - 4, 30, 8))
            pygame.draw.ellipse(screen, MUD_COLOR_DARK,
                                (mud_rect.x + 10, cy - 2, 20, 6))

        # Porterías
        self._draw_goal(screen, 'left')
        self._draw_goal(screen, 'right')

    def _draw_goal(self, screen, side):
        gx = 0 if side == 'left' else SW - GOAL_W

        # Red con cuadrícula
        net = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
        net.fill(GOAL_NET_COLOR)
        for i in range(0, GOAL_W, 10):
            pygame.draw.line(net, (200, 200, 200, 40), (i, 0), (i, GOAL_H), 1)
        for j in range(0, GOAL_H, 10):
            pygame.draw.line(net, (200, 200, 200, 40), (0, j), (GOAL_W, j), 1)
        screen.blit(net, (gx, GOAL_TOP_Y))

        # Travesaño
        pygame.draw.rect(screen, GOAL_COLOR,
                         (gx, GOAL_TOP_Y - GOAL_POST, GOAL_W, GOAL_POST))

        # Poste trasero
        px = gx if side == 'left' else gx + GOAL_W - GOAL_POST
        pygame.draw.rect(screen, GOAL_COLOR,
                         (px, GOAL_TOP_Y - GOAL_POST, GOAL_POST, GOAL_H + GOAL_POST))