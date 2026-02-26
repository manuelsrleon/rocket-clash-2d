import pygame
import Box2D
import math
from scene import PyGameScene
from factory import RocketFactory
from ingame_menu_scene import IngameMenu
from end_scene import EndScene
from assets_manager import SFXAssets
from settings import ScreenSettings, GUISettings, Colors, GameSettings, VolumeController
from pygame.locals import *

# Física Box2D

PPM = 10.0
TIME_STEP = 1.0 / 60.0
VEL_ITERS = 8
POS_ITERS = 3

def px2m(px):
    return px / PPM

def m2px(m):
    return m * PPM

# Pantalla
SW = ScreenSettings.SCREEN_WIDTH
SH = ScreenSettings.SCREEN_HEIGHT
GROUND_Y = 520

# Portería
GOAL_W = 60          
GOAL_H = 130
GOAL_POST = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H

# Posiciones iniciales
PLAYER_START = (200, GROUND_Y - 60)
BALL_START   = (SW // 2, GROUND_Y - 180)

# Movimiento
PLAYER_SPEED   = 8.0     # m/s velocidad objetivo
PLAYER_JUMP    = -12.0   # impulso vertical
GROUND_BLEND   = 0.25    # interpolación en suelo
AIR_BLEND      = 0.10    # interpolación en aire

# Colores
BG_COLOR       = (30, 120, 60)
GROUND_COLOR   = (20, 100, 50)
GOAL_COLOR     = (255, 255, 255)
GOAL_NET_COLOR = (180, 180, 180, 80)

# Pausa tras gol
GOAL_PAUSE_MS = 2000


def create_boundaries(world):
    """Suelo, techo y paredes (con hueco para porterías)."""
    # Suelo
    ground = world.CreateStaticBody(position=(px2m(SW / 2), px2m(GROUND_Y)))
    ground.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.6)

    # Techo
    ceiling = world.CreateStaticBody(position=(px2m(SW / 2), px2m(-5)))
    ceiling.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.2)

    # Pared izquierda – solo por encima de la portería
    wl = world.CreateStaticBody(position=(px2m(-5), px2m(GOAL_TOP_Y / 2)))
    wl.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

    # Pared derecha – solo por encima de la portería
    wr = world.CreateStaticBody(position=(px2m(SW + 5), px2m(GOAL_TOP_Y / 2)))
    wr.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)


def create_goal_bodies(world, side):
    """Crea travesaño, poste trasero y suelo de portería.
    Devuelve pygame.Rect del sensor de gol."""
    if side == 'left':
        gx = 0
    else:
        gx = SW - GOAL_W

    # Travesaño (barra horizontal superior)
    cx = px2m(gx + GOAL_W / 2)
    cy = px2m(GOAL_TOP_Y - GOAL_POST / 2)
    bar = world.CreateStaticBody(position=(cx, cy))
    bar.CreatePolygonFixture(
        box=(px2m(GOAL_W / 2), px2m(GOAL_POST / 2)),
        friction=0.4, restitution=0.3
    )

    # Poste trasero vertical (fondo de la portería)
    if side == 'left':
        px_post = gx - GOAL_POST / 2
    else:
        px_post = gx + GOAL_W + GOAL_POST / 2
    py_post = px2m(GOAL_TOP_Y + GOAL_H / 2)
    post = world.CreateStaticBody(position=(px2m(px_post), py_post))
    post.CreatePolygonFixture(
        box=(px2m(GOAL_POST / 2), px2m(GOAL_H / 2)),
        friction=0.4, restitution=0.3
    )

    # Suelo dentro de la portería
    floor = world.CreateStaticBody(position=(cx, px2m(GROUND_Y)))
    floor.CreatePolygonFixture(
        box=(px2m(GOAL_W / 2), px2m(5)),
        friction=0.6
    )

    return pygame.Rect(gx, GOAL_TOP_Y, GOAL_W, GOAL_H)



class MatchScene(PyGameScene):

    def __init__(self, director):
        super().__init__(director)

        # Mundo Box2D
        self.world = Box2D.b2World(gravity=(0, 25), doSleep=True)
        create_boundaries(self.world)

        # Porterías
        self.goal_l_rect = create_goal_bodies(self.world, 'left')
        self.goal_r_rect = create_goal_bodies(self.world, 'right')

        # Sprites usando RocketFactory (factory.py)
        self.jugador = RocketFactory.create_element("player", self.world, PLAYER_START)
        self.pelota  = RocketFactory.create_element("ball",   self.world, BALL_START)

        self.grupo_sprites = pygame.sprite.Group(self.jugador, self.pelota)

        # Control de movimiento
        self.move_left_flag  = False
        self.move_right_flag = False
        self.on_ground       = False

        # Marcador
        self.score_left  = 0
        self.score_right = 0

        # Temporizador
        self.time_remaining_ms = GameSettings.MATCH_DURATION * 1000
        self.match_over = False

        # Pausa tras gol
        self.goal_pause_timer = 0
        self.goal_scored = False

        # Fuentes
        self.font_score = pygame.font.SysFont(GUISettings.FONT_TEXT, 48, bold=True)
        self.font_timer = pygame.font.SysFont(GUISettings.FONT_TEXT, 28)
        self.font_goal  = pygame.font.SysFont(GUISettings.FONT_TEXT, 72, bold=True)


    def _body_px(self, body):
        return (m2px(body.position.x), m2px(body.position.y))

    def _sync_sprite(self, sprite):
        """Sincroniza sprite con Box2D usando establecerPosicion (car.py / ball.py)."""
        if sprite.body:
            pos = sprite.body.position
            sprite.establecerPosicion((m2px(pos.x), m2px(pos.y)))

    def _check_on_ground(self):
        if self.jugador.body:
            py = m2px(self.jugador.body.position.y)
            self.on_ground = py >= GROUND_Y - self.jugador.rect.height / 2 - 4

    def _apply_player_movement(self):
        if not self.jugador.body:
            return

        vel = self.jugador.body.linearVelocity
        target_vx = 0.0
        if self.move_left_flag:
            target_vx -= PLAYER_SPEED
        if self.move_right_flag:
            target_vx += PLAYER_SPEED

        blend = GROUND_BLEND if self.on_ground else AIR_BLEND
        new_vx = vel.x + (target_vx - vel.x) * blend
        self.jugador.body.linearVelocity = (new_vx, vel.y)


    def _check_goals(self):
        if self.goal_scored:
            return
        bx, by = self._body_px(self.pelota.body)
        if self.goal_l_rect.collidepoint(bx, by):
            self.score_right += 1
            self._on_goal()
        elif self.goal_r_rect.collidepoint(bx, by):
            self.score_left += 1
            self._on_goal()

    def _on_goal(self):
        self.goal_scored = True
        self.goal_pause_timer = GOAL_PAUSE_MS
        try:
            sound = SFXAssets.goal1.play()
            sound.set_volume(VolumeController.get_current_volume())
        except Exception:
            pass

    def _reset_positions(self):
        """Recoloca jugador y pelota tras gol."""
        self.jugador.body.position = (px2m(PLAYER_START[0]), px2m(PLAYER_START[1]))
        self.jugador.body.linearVelocity = (0, 0)
        self.jugador.body.angularVelocity = 0

        self.pelota.body.position = (px2m(BALL_START[0]), px2m(BALL_START[1]))
        self.pelota.body.linearVelocity = (0, 0)
        self.pelota.body.angularVelocity = 0

        self.move_left_flag = False
        self.move_right_flag = False


    def events(self, event_list):
        for ev in event_list:
            if ev.type == QUIT:
                self.director.salirPrograma()

            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    self.director.apilarEscena(IngameMenu(self.director))
                elif not self.goal_scored:
                    if ev.key == K_a or ev.key == K_LEFT:
                        self.move_left_flag = True
                    elif ev.key == K_d or ev.key == K_RIGHT:
                        self.move_right_flag = True
                    elif ev.key == K_w or ev.key == K_UP or ev.key == K_SPACE:
                        if self.on_ground:
                            vel = self.jugador.body.linearVelocity
                            self.jugador.body.linearVelocity = (vel.x, PLAYER_JUMP)

            elif ev.type == KEYUP:
                if ev.key == K_a or ev.key == K_LEFT:
                    self.move_left_flag = False
                elif ev.key == K_d or ev.key == K_RIGHT:
                    self.move_right_flag = False

    def update(self, delta_time):
        if self.match_over:
            return

        # Pausa tras gol
        if self.goal_scored:
            self.goal_pause_timer -= delta_time
            if self.goal_pause_timer <= 0:
                self.goal_scored = False
                self._reset_positions()
            return

        dt = delta_time / 1000.0

        self._apply_player_movement()

        self.world.Step(TIME_STEP, VEL_ITERS, POS_ITERS)
        self.world.ClearForces()

        for sprite in self.grupo_sprites:
            self._sync_sprite(sprite)
            sprite.update(dt)

        self._check_on_ground()

        self._check_goals()

        self.time_remaining_ms -= delta_time
        if self.time_remaining_ms <= 0:
            self.time_remaining_ms = 0
            self.match_over = True
            if self.score_left > self.score_right:
                result = "winner_1"
            elif self.score_right > self.score_left:
                result = "winner_2"
            else:
                result = "tie"
            self.director.apilarEscena(EndScene(self.director, result=result))

  
    def render(self, screen):
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SW, SH - GROUND_Y))

        # Línea central y círculo
        pygame.draw.line(screen, (255, 255, 255), (SW // 2, 0), (SW // 2, GROUND_Y), 1)
        pygame.draw.circle(screen, (255, 255, 255), (SW // 2, GROUND_Y - 120), 60, 1)

        # Porterías
        self._draw_goal(screen, 'left')
        self._draw_goal(screen, 'right')

        # Sprites (PlayerCar, Ball) via pygame.sprite.Group.draw()
        self.grupo_sprites.draw(screen)

        # HUD
        self._draw_hud(screen)

        if self.goal_scored:
            self._draw_goal_text(screen)

    def _draw_goal(self, screen, side):
        if side == 'left':
            gx = 0
        else:
            gx = SW - GOAL_W

        # Red de fondo
        net = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
        net.fill(GOAL_NET_COLOR)
        # Líneas verticales de red
        for i in range(0, GOAL_W, 10):
            pygame.draw.line(net, (200, 200, 200, 50), (i, 0), (i, GOAL_H), 1)
        # Líneas horizontales de red
        for j in range(0, GOAL_H, 10):
            pygame.draw.line(net, (200, 200, 200, 50), (0, j), (GOAL_W, j), 1)
        screen.blit(net, (gx, GOAL_TOP_Y))

        # Travesaño
        pygame.draw.rect(screen, GOAL_COLOR,
                         (gx, GOAL_TOP_Y - GOAL_POST, GOAL_W, GOAL_POST))

        # Poste trasero
        if side == 'left':
            px = gx
        else:
            px = gx + GOAL_W - GOAL_POST
        pygame.draw.rect(screen, GOAL_COLOR,
                         (px, GOAL_TOP_Y - GOAL_POST, GOAL_POST, GOAL_H + GOAL_POST))

    def _draw_hud(self, screen):
        # Marcador
        txt = f"{self.score_left}  -  {self.score_right}"
        surf = self.font_score.render(txt, True, Colors.WHITE)
        r = surf.get_rect(centerx=SW // 2, top=12)
        screen.blit(surf, r)

        # Temporizador
        secs = max(0, self.time_remaining_ms // 1000)
        m, s = divmod(secs, 60)
        color = Colors.LIGHT_RED if secs <= 15 else Colors.WHITE
        tsurf = self.font_timer.render(f"{m}:{s:02d}", True, color)
        tr = tsurf.get_rect(centerx=SW // 2, top=66)
        screen.blit(tsurf, tr)

    def _draw_goal_text(self, screen):
        shadow = self.font_goal.render("¡GOL!", True, Colors.BLACK)
        text   = self.font_goal.render("¡GOL!", True, Colors.YELLOW)
        cx, cy = SW // 2, SH // 2
        screen.blit(shadow, shadow.get_rect(center=(cx + 3, cy + 3)))
        screen.blit(text,   text.get_rect(center=(cx, cy)))