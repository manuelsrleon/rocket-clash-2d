import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
from ingame_menu_scene import IngameMenu
from end_scene import EndScene
from assets_manager import SFXAssets
from settings import ScreenSettings, GUISettings, Colors, GameSettings, VolumeController
from pygame.locals import *
import random

# Física Box2D
PPM = 10.0

def px2m(px): return px / PPM
def m2px(m):  return m  * PPM

# Pantalla
SW = ScreenSettings.SCREEN_WIDTH
SH = ScreenSettings.SCREEN_HEIGHT

# ─── POWER-UP BASE ───────────────────────────────────────────
POWERUP_BOX_SIZE     = 30       # px lado de la caja
POWERUP_FALL_SPEED   = 3.0     # m/s velocidad de caída
POWERUP_SPAWN_INTERVAL = 30000 # ms entre spawns
POWERUP_COLOR        = (255, 200, 0)
POWERUP_BORDER_COLOR = (200, 150, 0)
POWERUP_GLOW_COLOR   = (255, 255, 100, 80)


class PowerUpBox(pygame.sprite.Sprite):
    """Caja de power-up que cae del cielo. Es un sensor Box2D."""

    def __init__(self, world, x_px, ground_y_px, size=POWERUP_BOX_SIZE):
        super().__init__()
        self.size = size
        self.ground_y_px = ground_y_px

        # Superficie visual
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._draw_box()
        self.rect = self.image.get_rect()
        self.rect.centerx = int(x_px)
        self.rect.centery = 0  # empieza arriba

        # Body Box2D — sensor cinemático que cae
        cx_m = px2m(x_px)
        cy_m = px2m(-size)  # empieza fuera de pantalla
        self.body = world.CreateKinematicBody(position=(cx_m, cy_m))
        self.body.CreatePolygonFixture(
            box=(px2m(size / 2), px2m(size / 2)),
            isSensor=True,
            userData={'type': 'powerup'}
        )
        self.body.linearVelocity = (0, POWERUP_FALL_SPEED)

        self.collected = False

    def _draw_box(self):
        """Dibuja la caja con un aspecto de power-up."""
        s = self.size
        # Fondo
        pygame.draw.rect(self.image, POWERUP_COLOR, (0, 0, s, s), border_radius=4)
        # Borde
        pygame.draw.rect(self.image, POWERUP_BORDER_COLOR, (0, 0, s, s), 2, border_radius=4)
        # Símbolo "?" o "⚡"
        font = pygame.font.SysFont('Arial', s - 8, bold=True)
        symbol = font.render("⚡", True, (100, 50, 0))
        self.image.blit(symbol, symbol.get_rect(center=(s // 2, s // 2)))

    def establecerPosicion(self, pos):
        self.rect.centerx = int(pos[0])
        self.rect.centery = int(pos[1])

    def update(self, dt):
        pass  # movimiento gestionado por Box2D kinematic body

    def has_landed(self):
        """Devuelve True si la caja llegó al suelo."""
        return m2px(self.body.position.y) >= self.ground_y_px


class MatchScene(PyGameScene):
    """Clase base para todas las escenas de partido.
    Las subclases (first_scene, second_scene...) deben implementar:
      - _get_config()       → dict con constantes del escenario
      - _create_boundaries() → cuerpos estáticos del campo
      - _create_goals()      → cuerpos de porterías, devuelve (rect_l, rect_r)
      - _render_field(screen) → dibujo visual del campo
    Opcionalmente:
      - _on_powerup_collected() → lógica específica del power-up del escenario
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

        # ─── Power-up base ────────────────────────────────────
        self.powerup_spawn_timer = POWERUP_SPAWN_INTERVAL
        self.active_powerup = None          # PowerUpBox actual (o None)
        self.player_has_powerup = False     # True si el jugador recogió el power-up

        # Hook para que subclases añadan elementos extra (boss, etc.)
        self._init_extras()

        # Marcador
        self.score_left  = 0
        self.score_right = 0

        # Temporizador
        self.time_remaining_ms = GameSettings.MATCH_DURATION * 1000
        self.match_over = False

        # Pausa tras gol
        self.goal_pause_timer = 0
        self.goal_scored      = False

        # GUISettings.FONT_TEXT (settings.py)
        self.font_score = pygame.font.SysFont(GUISettings.FONT_TEXT, 48, bold=True)
        self.font_timer = pygame.font.SysFont(GUISettings.FONT_TEXT, 28)
        self.font_goal  = pygame.font.SysFont(GUISettings.FONT_TEXT, 72, bold=True)
        self.font_powerup = pygame.font.SysFont(GUISettings.FONT_TEXT, 16, bold=True)

    def _get_config(self):
        return {}

    def _create_boundaries(self):
        pass

    def _create_goals(self):
        return (pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0))

    def _render_field(self, screen):
        screen.fill(Colors.BLACK)

    def _init_extras(self):
        pass

    def _body_px(self, body):
        return (m2px(body.position.x), m2px(body.position.y))

    def _sync_sprite(self, sprite):
        if sprite.body:
            pos = sprite.body.position
            sprite.establecerPosicion((m2px(pos.x), m2px(pos.y)))

    def _check_on_ground(self):
        if not self.jugador.body:
            return
        ground_m = px2m(self.ground_y)

        bottom_m = self.jugador.body.position.y + self.player_hh
        self.jugador.on_ground = bottom_m >= ground_m - 1.0

        for sprite in self.grupo_sprites:
            if sprite is self.jugador or sprite is self.pelota:
                continue
            if hasattr(sprite, 'body') and sprite.body and hasattr(sprite, 'on_ground'):
                hh = sprite.rect.height / 2 / PPM
                bottom = sprite.body.position.y + hh
                sprite.on_ground = bottom >= ground_m - 1.0

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

    # ─── POWER-UP SISTEMA BASE ────────────────────────────────

    def _spawn_powerup(self):
        """Genera una caja de power-up en una posición X aleatoria."""
        if self.active_powerup is not None:
            return  # ya hay una caja activa
        margin = 100
        x = random.randint(margin, SW - margin)
        box = PowerUpBox(self.world, x, self.ground_y)
        self.active_powerup = box
        self.grupo_sprites.add(box)

    def _destroy_powerup(self):
        """Elimina la caja activa del mundo y del grupo de sprites."""
        if self.active_powerup is None:
            return
        if self.active_powerup.body:
            self.world.DestroyBody(self.active_powerup.body)
            self.active_powerup.body = None
        self.active_powerup.kill()  # elimina del sprite group
        self.active_powerup = None

    def _check_powerup_collision(self):
        """Comprueba si el jugador toca la caja de power-up por proximidad."""
        if self.active_powerup is None or self.active_powerup.collected:
            return
        if not self.jugador.body or not self.active_powerup.body:
            return

        player_pos = self.jugador.body.position
        box_pos = self.active_powerup.body.position

        dx = abs(player_pos.x - box_pos.x)
        dy = abs(player_pos.y - box_pos.y)

        # Umbral: mitad del jugador + mitad de la caja
        threshold_x = px2m(self.jugador.rect.width / 2 + self.active_powerup.size / 2)
        threshold_y = px2m(self.jugador.rect.height / 2 + self.active_powerup.size / 2)

        if dx < threshold_x and dy < threshold_y:
            self.active_powerup.collected = True
            self.player_has_powerup = True
            self._destroy_powerup()
            self._on_powerup_collected()

    def _on_powerup_collected(self):
        """Hook para subclases: lógica específica al recoger el power-up."""
        pass

    def _update_powerup(self, delta_time):
        """Actualiza el sistema de power-ups: timer de spawn, caída, recolección."""
        # Timer de spawn
        self.powerup_spawn_timer -= delta_time
        if self.powerup_spawn_timer <= 0:
            self.powerup_spawn_timer = POWERUP_SPAWN_INTERVAL
            self._spawn_powerup()

        # Actualizar caja activa
        if self.active_powerup is not None and not self.active_powerup.collected:
            # Sincronizar posición visual
            self._sync_sprite(self.active_powerup)

            # Si llegó al suelo, detener caída
            if self.active_powerup.has_landed():
                self.active_powerup.body.linearVelocity = (0, 0)
                ground_m = px2m(self.ground_y - self.active_powerup.size / 2)
                self.active_powerup.body.position = (
                    self.active_powerup.body.position.x, ground_m
                )

            # Comprobar si el jugador la toca
            self._check_powerup_collision()

    def _render_powerup_hud(self, screen):
        """Dibuja un indicador en el HUD si el jugador tiene un power-up disponible."""
        if self.player_has_powerup:
            text = self.font_powerup.render("⚡ POWER-UP LISTO [E]", True, POWERUP_COLOR)
            rect = text.get_rect(bottomleft=(10, SH - 10))
            bg = pygame.Surface((rect.width + 12, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            screen.blit(bg, (rect.x - 6, rect.y - 4))
            screen.blit(text, rect)

    # ─── EVENTS ───────────────────────────────────────────────

    def events(self, event_list):
        for ev in event_list:
            if ev.type == KEYDOWN:
                if ev.key == K_LEFT or ev.key == K_a:
                    self.move_left_flag = True
                elif ev.key == K_RIGHT or ev.key == K_d:
                    self.move_right_flag = True
                elif ev.key == K_UP or ev.key == K_w or ev.key == K_SPACE:
                    if self.jugador.on_ground and self.jugador.body:
                        vel = self.jugador.body.linearVelocity
                        self.jugador.body.linearVelocity = (vel.x, self.player_jump)
                elif ev.key == K_e:
                    self._on_powerup_activate()
                elif ev.key == K_ESCAPE:
                    self.director.apilarEscena(IngameMenu(self.director))
            elif ev.type == KEYUP:
                if ev.key == K_LEFT or ev.key == K_a:
                    self.move_left_flag = False
                elif ev.key == K_RIGHT or ev.key == K_d:
                    self.move_right_flag = False

    def _on_powerup_activate(self):
        """Hook para subclases: se llama cuando el jugador pulsa E para usar el power-up."""
        pass

    # ─── UPDATE ───────────────────────────────────────────────

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

        self._check_on_ground()
        self._check_goals()
        self._update_powerup(delta_time)

        self.time_remaining_ms -= delta_time
        if self.time_remaining_ms <= 0:
            self.time_remaining_ms = 0
            self.match_over = True
            self.director.change_scene(EndScene(
                self.director, self.score_left, self.score_right
            ))

    # ─── RENDER ───────────────────────────────────────────────
    def _render_field_fg(self, screen):
        pass

    def render(self, screen):
        self._render_field(screen)
        self.grupo_sprites.draw(screen)
        self._render_field_fg(screen)
        self._draw_hud(screen)
        self._render_powerup_hud(screen)

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