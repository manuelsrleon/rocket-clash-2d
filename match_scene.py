import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
from ingame_menu_scene import IngameMenu
from end_scene import EndScene
from assets_manager import SFXAssets
from settings import ScreenSettings, GUISettings, Colors, GameSettings, VolumeController
from pygame.locals import *

# Física Box2D
PPM = 10.0

def px2m(px): return px / PPM
def m2px(m):  return m  * PPM

# Pantalla
SW = ScreenSettings.SCREEN_WIDTH
SH = ScreenSettings.SCREEN_HEIGHT


class MatchScene(PyGameScene):
    """Clase base para todas las escenas de partido.
    Las subclases (first_scene, second_scene...) deben implementar:
      - _get_config()       → dict con constantes del escenario
      - _create_boundaries() → cuerpos estáticos del campo
      - _create_goals()      → cuerpos de porterías, devuelve (rect_l, rect_r)
      - _render_field(screen) → dibujo visual del campo
    """

    def __init__(self, director):
        super().__init__(director)

        # Config del escenario
        cfg = self._get_config()
        self.ground_y     = cfg.get('ground_y', 520)
        self.player_start = cfg.get('player_start', (200, 460))
        self.ball_start   = cfg.get('ball_start', (SW // 2, 300))
        self.gravity      = cfg.get('gravity', (0, 35))
        self.player_speed = cfg.get('player_speed', 12.0)
        self.player_jump  = cfg.get('player_jump', -18.0)
        self.ground_blend = cfg.get('ground_blend', 0.35)
        self.air_blend    = cfg.get('air_blend', 0.12)
        self.player_hh    = cfg.get('player_hh', 3.5)
        self.goal_pause   = cfg.get('goal_pause_ms', 2000)

        # Mundo Box2D
        self.world = Box2D.b2World(gravity=self.gravity, doSleep=True)

        # Campo y porterías (implementado por subclase)
        self._create_boundaries()
        self.goal_l_rect, self.goal_r_rect = self._create_goals()

        # Sprites via RocketFactory (factory.py)
        self.jugador = RocketFactory.create_element("player", self.world, self.player_start)
        self.pelota  = RocketFactory.create_element("ball",   self.world, self.ball_start)
        self.grupo_sprites = pygame.sprite.Group(self.jugador, self.pelota)

        # Flags de movimiento
        self.move_left_flag  = False
        self.move_right_flag = False

        # Marcador
        self.score_left  = 0
        self.score_right = 0

        # Temporizador GameSettings.MATCH_DURATION (settings.py)
        self.time_remaining_ms = GameSettings.MATCH_DURATION * 1000
        self.match_over = False

        # Pausa tras gol
        self.goal_pause_timer = 0
        self.goal_scored      = False

        # GUISettings.FONT_TEXT (settings.py)
        self.font_score = pygame.font.SysFont(GUISettings.FONT_TEXT, 48, bold=True)
        self.font_timer = pygame.font.SysFont(GUISettings.FONT_TEXT, 28)
        self.font_goal  = pygame.font.SysFont(GUISettings.FONT_TEXT, 72, bold=True)


    def _get_config(self):
        """Devuelve dict con constantes del escenario."""
        return {}

    def _create_boundaries(self):
        """Crea los cuerpos estáticos del campo (suelo, techo, paredes)."""
        pass

    def _create_goals(self):
        """Crea porterías. Devuelve (goal_l_rect, goal_r_rect)."""
        return (pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0))

    def _render_field(self, screen):
        """Dibuja el fondo y decoración del campo."""
        screen.fill(Colors.BLACK)


    def _body_px(self, body):
        return (m2px(body.position.x), m2px(body.position.y))

    def _sync_sprite(self, sprite):
        if sprite.body:
            pos = sprite.body.position
            sprite.establecerPosicion((m2px(pos.x), m2px(pos.y)))

    def _check_on_ground(self):
        if not self.jugador.body:
            return
        bottom_m = self.jugador.body.position.y + self.player_hh
        ground_m = px2m(self.ground_y)
        self.jugador.on_ground = bottom_m >= ground_m - 1.0

    def _apply_player_movement(self):
        if not self.jugador.body:
            return
        vel = self.jugador.body.linearVelocity
        target_vx = 0.0
        if self.move_left_flag:
            target_vx = -self.player_speed
        if self.move_right_flag:
            target_vx =  self.player_speed
        blend  = self.ground_blend if self.jugador.on_ground else self.air_blend
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
        self.goal_scored      = True
        self.goal_pause_timer = self.goal_pause
        try:
            sound = SFXAssets.goal1.play()
            sound.set_volume(VolumeController.get_current_volume())
        except Exception:
            pass

    def _reset_positions(self):
        self.jugador.body.position        = (px2m(self.player_start[0]), px2m(self.player_start[1]))
        self.jugador.body.linearVelocity  = (0, 0)
        self.jugador.body.angularVelocity = 0
        self.pelota.body.position         = (px2m(self.ball_start[0]), px2m(self.ball_start[1]))
        self.pelota.body.linearVelocity   = (0, 0)
        self.pelota.body.angularVelocity  = 0
        self.move_left_flag  = False
        self.move_right_flag = False


    def events(self, event_list):
        for ev in event_list:
            if ev.type == QUIT:
                self.director.salirPrograma()
            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    self.director.apilarEscena(IngameMenu(self.director))
                elif not self.goal_scored:
                    if ev.key in (K_a, K_LEFT):
                        self.move_left_flag = True
                    elif ev.key in (K_d, K_RIGHT):
                        self.move_right_flag = True
                    elif ev.key in (K_w, K_UP, K_SPACE):
                        if self.jugador.on_ground:
                            vel = self.jugador.body.linearVelocity
                            self.jugador.body.linearVelocity = (vel.x, self.player_jump)
            elif ev.type == KEYUP:
                if ev.key in (K_a, K_LEFT):
                    self.move_left_flag = False
                elif ev.key in (K_d, K_RIGHT):
                    self.move_right_flag = False


    def update(self, delta_time):
        if self.match_over:
            return

        if self.goal_scored:
            self.goal_pause_timer -= delta_time
            if self.goal_pause_timer <= 0:
                self.goal_scored = False
                self._reset_positions()
            return

        self._apply_player_movement()

        self.world.Step(1.0 / 60.0, 8, 3)
        self.world.ClearForces()

        dt = delta_time / 1000.0
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

    #  RENDER
    def render(self, screen):
        # Campo (implementado por subclase)
        self._render_field(screen)

        # Sprites: PlayerCar + Ball
        self.grupo_sprites.draw(screen)

        # HUD
        self._draw_hud(screen)

        if self.goal_scored:
            self._draw_goal_text(screen)

    def _draw_hud(self, screen):
        surf = self.font_score.render(
            f"{self.score_left}  -  {self.score_right}", True, Colors.WHITE
        )
        screen.blit(surf, surf.get_rect(centerx=SW // 2, top=12))

        secs  = max(0, self.time_remaining_ms // 1000)
        m, s  = divmod(secs, 60)
        color = Colors.LIGHT_RED if secs <= 15 else Colors.WHITE
        tsurf = self.font_timer.render(f"{m}:{s:02d}", True, color)
        screen.blit(tsurf, tsurf.get_rect(centerx=SW // 2, top=66))

    def _draw_goal_text(self, screen):
        shadow = self.font_goal.render("¡GOL!", True, Colors.BLACK)
        text   = self.font_goal.render("¡GOL!", True, Colors.YELLOW)
        cx, cy = SW // 2, SH // 2
        screen.blit(shadow, shadow.get_rect(center=(cx + 3, cy + 3)))
        screen.blit(text,   text.get_rect(center=(cx, cy)))