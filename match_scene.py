import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
from ingame_menu_scene import IngameMenu
from end_scene import EndScene
from assets_manager import Assets
from settings import ScreenSettings, GUISettings, Colors, GameSettings, VolumeController
from pygame.locals import *
from pygame import Color
from physics_debug_renderer import PhysicsDebugRenderer
import random
import os

# Fisica Box2D
PPM = 10.0

def px2m(px): return px / PPM
def m2px(m):  return m  * PPM

# Pantalla
SW = ScreenSettings.SCREEN_WIDTH
SH = ScreenSettings.SCREEN_HEIGHT

# --- POWER-UP BASE ---
POWERUP_BOX_SIZE       = 30      # px lado de la caja
POWERUP_FALL_SPEED     = 3.0     # m/s velocidad de caida
POWERUP_SPAWN_INTERVAL = 10000   # ms entre spawns
POWERUP_COLOR          = (255, 200, 0)
POWERUP_BORDER_COLOR   = (200, 150, 0)
POWERUP_GLOW_COLOR     = (255, 255, 100, 80)


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

        # Body Box2D - delegado a RocketFactory
        self.body = RocketFactory.create_powerup_body(world, x_px, size)
        self.body.linearVelocity = (0, POWERUP_FALL_SPEED)

        self.collected = False

    def _draw_box(self):
        """Dibuja la caja con un aspecto de power-up."""
        s = self.size
        # Fondo
        pygame.draw.rect(self.image, POWERUP_COLOR, (0, 0, s, s), border_radius=4)
        # Borde
        pygame.draw.rect(self.image, POWERUP_BORDER_COLOR, (0, 0, s, s), 2, border_radius=4)
        # Simbolo "?"
        font = pygame.font.SysFont('Arial', s - 8, bold=True)
        symbol = font.render("?", True, (100, 50, 0))
        self.image.blit(symbol, symbol.get_rect(center=(s // 2, s // 2)))

    def establecerPosicion(self, pos):
        self.rect.centerx = int(pos[0])
        self.rect.centery = int(pos[1])

    def update(self, dt):
        pass  # movimiento gestionado por Box2D kinematic body

    def has_landed(self):
        """Devuelve True si la caja llego al suelo."""
        return m2px(self.body.position.y) >= self.ground_y_px


class MatchScene(PyGameScene):
    """Clase base para todas las escenas de partido.
    Las subclases (first_scene, second_scene...) deben implementar:
      - _get_config()        -> dict con constantes del escenario
      - _create_boundaries() -> cuerpos estaticos del campo
      - _create_goals()      -> cuerpos de porterias, devuelve (rect_l, rect_r)
      - _render_field(screen)-> dibujo visual del campo
    Opcionalmente:
      - _on_powerup_collected() -> logica especifica del power-up del escenario
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
        self.PHYSICS_DEBUG_MODE = False

        # Campo y porterias (implementado por subclase)
        self._create_boundaries()
        self.goal_l_rect, self.goal_r_rect = self._create_goals()

        # Sprites via RocketFactory (factory.py)
        self.jugador = RocketFactory.create_element("player", self.world, self.player_start)
        self.pelota  = RocketFactory.create_element("ball",   self.world, self.ball_start)
        self.grupo_sprites = pygame.sprite.Group(self.jugador, self.pelota)

        # Sprites who cast shadows
        self.shadow_sprites = [self.jugador]

        # Flags de movimiento
        self.move_left_flag  = False
        self.move_right_flag = False

        # --- Power-up base ---
        self.powerup_spawn_timer = POWERUP_SPAWN_INTERVAL
        self.active_powerup = None          # PowerUpBox actual (o None)
        self.player_has_powerup = False     # True si el jugador recogio el power-up

        # Hook para que subclases anadan elementos extra (boss, etc.)
        self._init_extras()
        self._align_boss_visual_with_player()

        # Marcador
        self.score_left  = 0
        self.score_right = 0

        # Temporizador
        self.time_remaining_ms = GameSettings.MATCH_DURATION * 1000
        self.match_over = False

        # Pausa tras gol
        self.goal_pause_timer = 0
        self.goal_scored      = False

        # --- Ball stuck detection
        self._ball_stuck_timer_ms = 0
        self._ball_stuck_threshold_ms = 3000
        self._ball_stuck_speed_threshold = 0.65
        self._kickoff_speed = 6.0

        # Fuentes
        self.font_score = pygame.font.SysFont(GUISettings.FONT_TEXT, 48, bold=True)
        self.font_timer = pygame.font.SysFont(GUISettings.FONT_TEXT, 28)
        self.font_goal  = pygame.font.SysFont(GUISettings.FONT_TEXT, 72, bold=True)
        self.font_powerup = pygame.font.SysFont(GUISettings.FONT_TEXT, 16, bold=True)

        # Musica de fondo
        self._start_background_music()

        # Countdown inicial
        self.intro_countdown_timer = 3500  # 3.5 segundos (3, 2, 1, YA)
        self.waiting_for_intro = True

        # Transicion
        self.fade_from_black()

        # Estado de salida
        self.is_exiting = False
        self.wait_timer = 0

        # Secuencia de cierre: FIN DEL PARTIDO (4s) -> RESULTADO (4s) -> fade
        self.end_phase = None            # "fin", "result" o None
        self.end_phase_timer_ms = 0
        self.result_text = ""
        self.result_color = Colors.WHITE
        self.fade_started = False

    def on_exit(self):
        """Se llama cuando se sale de la escena"""
        self._stop_background_music()

    def _start_background_music(self):
        try:
            cfg = self._get_config()
            music_key = cfg.get('music_name', "musica2")
            music_path = Assets.get_music_path(music_key)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(VolumeController.get_music_volume())
            pygame.mixer.music.play(-1)  # -1 para loop infinito
        except Exception as e:
            print(f"Error al cargar musica de fondo: {e}")

    def _stop_background_music(self):
        """Detiene la musica de fondo"""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

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

    def _get_body_bottom_local_m(self, body):
        bottom = 0.0
        for fixture in body.fixtures:
            shape = fixture.shape
            if isinstance(shape, Box2D.b2PolygonShape):
                y = max(v[1] for v in shape.vertices)
            elif isinstance(shape, Box2D.b2CircleShape):
                y = shape.pos[1] + shape.radius
            else:
                continue
            if y > bottom:
                bottom = y
        return bottom

    def _get_visual_sink_px(self, sprite):
        if not getattr(sprite, 'body', None):
            return 0
        half_h_m = (sprite.rect.height / 2) / PPM
        body_bottom_m = self._get_body_bottom_local_m(sprite.body)
        sink_m = half_h_m - body_bottom_m
        return int(round(sink_m * PPM))

    def _align_boss_visual_with_player(self):
        boss = getattr(self, 'boss', None)
        if boss is None or not getattr(boss, 'body', None) or not self.jugador.body:
            return

        player_sink = self._get_visual_sink_px(self.jugador)
        boss_sink = self._get_visual_sink_px(boss)
        boss.render_offset_y = player_sink - boss_sink

    def _sync_sprite(self, sprite):
        if sprite.body:
            pos = sprite.body.position
            offset_y = getattr(sprite, 'render_offset_y', 0)
            sprite.establecerPosicion((m2px(pos.x), m2px(pos.y) + offset_y))

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
            target_vx = self.player_speed
        blend = self.ground_blend if self.jugador.on_ground else self.air_blend
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

    # --- BALL STUCK / KICKOFF HELPERS ---
    def _is_ball_in_goal_zone(self):
        bx, by = self._body_px(self.pelota.body)
        if self.goal_l_rect.collidepoint(bx, by) or self.goal_r_rect.collidepoint(bx, by):
            return True

        roof_margin_y = 40
        roof_margin_x = 12

        gl = self.goal_l_rect
        gr = self.goal_r_rect

        if (gl.left - roof_margin_x) <= bx <= (gl.right + roof_margin_x) and by <= (gl.top + roof_margin_y):
            return True
        if (gr.left - roof_margin_x) <= bx <= (gr.right + roof_margin_x) and by <= (gr.top + roof_margin_y):
            return True

        return False

    def _do_kickoff(self):
        if not self.pelota.body:
            return
        center_x = px2m(SW // 2)
        center_y = px2m(self.ground_y - 220)
        self.pelota.body.position = (center_x, center_y)
        self.pelota.body.linearVelocity = (0, 0)
        self.pelota.body.angularVelocity = 0

        dir_x = random.choice([-1.0, 1.0])
        vy = random.uniform(-0.5, 0.5)
        vx = dir_x * self._kickoff_speed
        self.pelota.body.linearVelocity = (vx, vy)

    def _check_ball_stuck(self, delta_time):
        if not hasattr(self, 'pelota') or not self.pelota.body:
            return

        if self._is_ball_in_goal_zone():
            vel = self.pelota.body.linearVelocity
            speed = (vel.x ** 2 + vel.y ** 2) ** 0.5
            if speed <= self._ball_stuck_speed_threshold:
                self._ball_stuck_timer_ms += delta_time
                if self._ball_stuck_timer_ms >= self._ball_stuck_threshold_ms:
                    self._ball_stuck_timer_ms = 0
                    self._do_kickoff()
        else:
            self._ball_stuck_timer_ms = 0

    def _on_goal(self):
        self.goal_scored = True
        self.goal_pause_timer = self.goal_pause

    def _reset_positions(self):
        self.jugador.body.position        = (px2m(self.player_start[0]), px2m(self.player_start[1]))
        self.jugador.body.linearVelocity  = (0, 0)
        self.jugador.body.angularVelocity = 0
        self.pelota.body.position         = (px2m(self.ball_start[0]), px2m(self.ball_start[1]))
        self.pelota.body.linearVelocity   = (0, 0)
        self.pelota.body.angularVelocity  = 0
        self.move_left_flag = False
        self.move_right_flag = False

    # --- POWER-UP SISTEMA BASE ---
    def _spawn_powerup(self):
        if self.active_powerup is not None:
            return
        margin = 100
        x = random.randint(margin, SW - margin)
        box = PowerUpBox(self.world, x, self.ground_y)
        self.active_powerup = box
        self.grupo_sprites.add(box)

    def _destroy_powerup(self):
        if self.active_powerup is None:
            return
        if self.active_powerup.body:
            RocketFactory.destroy_body(self.world, self.active_powerup.body)
            self.active_powerup.body = None
        self.active_powerup.kill()
        self.active_powerup = None

    def _check_powerup_collision(self):
        if self.active_powerup is None or self.active_powerup.collected:
            return
        if not self.jugador.body or not self.active_powerup.body:
            return

        player_pos = self.jugador.body.position
        box_pos = self.active_powerup.body.position

        dx = abs(player_pos.x - box_pos.x)
        dy = abs(player_pos.y - box_pos.y)

        threshold_x = px2m(self.jugador.rect.width / 2 + self.active_powerup.size / 2)
        threshold_y = px2m(self.jugador.rect.height / 2 + self.active_powerup.size / 2)

        if dx < threshold_x and dy < threshold_y:
            self.active_powerup.collected = True
            self.player_has_powerup = True
            self._destroy_powerup()
            self._on_powerup_collected()

    def _on_powerup_collected(self):
        pass

    def _update_powerup(self, delta_time):
        self.powerup_spawn_timer -= delta_time
        if self.powerup_spawn_timer <= 0:
            self.powerup_spawn_timer = POWERUP_SPAWN_INTERVAL
            self._spawn_powerup()

        if self.active_powerup is not None and not self.active_powerup.collected:
            self._sync_sprite(self.active_powerup)

            if self.active_powerup.has_landed():
                self.active_powerup.body.linearVelocity = (0, 0)
                ground_m = px2m(self.ground_y - self.active_powerup.size / 2)
                self.active_powerup.body.position = (
                    self.active_powerup.body.position.x, ground_m
                )

            self._check_powerup_collision()

    def _render_powerup_hud(self, screen):
        if self.player_has_powerup:
            text = self.font_powerup.render("POWER-UP LISTO [E]", True, POWERUP_COLOR)
            rect = text.get_rect(topleft=(10, 10))
            bg = pygame.Surface((rect.width + 12, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            screen.blit(bg, (rect.x - 6, rect.y - 4))
            screen.blit(text, rect)

    # --- EVENTS ---
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
                elif ev.key == K_p:
                    self.PHYSICS_DEBUG_MODE = not self.PHYSICS_DEBUG_MODE
            elif ev.type == KEYUP:
                if ev.key == K_LEFT or ev.key == K_a:
                    self.move_left_flag = False
                elif ev.key == K_RIGHT or ev.key == K_d:
                    self.move_right_flag = False

    def _on_powerup_activate(self):
        pass

    # --- UPDATE ---
    def update(self, delta_time):
        dt_sec = delta_time / 1000.0
        self.update_fade(delta_time)

        if self.is_exiting:
            # Espera final en negro antes del salto
            if self.wait_timer > 0:
                self.wait_timer -= dt_sec
                if self.wait_timer <= 0:
                    self._execute_scene_jump()
                return

            # Secuencia de textos (4s cada uno)
            if self.end_phase in ("fin", "result"):
                self.end_phase_timer_ms -= delta_time
                if self.end_phase_timer_ms <= 0:
                    if self.end_phase == "fin":
                        self.end_phase = "result"
                        self.end_phase_timer_ms = 4000
                    else:
                        self.end_phase = None
                return

            # Al terminar los textos, arrancar fade una sola vez
            if not self.fade_started:
                pygame.mixer.music.fadeout(2000)
                self.fade_to_black(callback=self._set_wait_timer)
                self.fade_started = True
            return

        if self.waiting_for_intro:
            if self.fade_alpha <= 0:
                self.intro_countdown_timer -= delta_time
                if self.intro_countdown_timer <= 0:
                    self.waiting_for_intro = False
            for sprite in self.grupo_sprites:
                self._sync_sprite(sprite)
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

        for sprite in self.grupo_sprites:
            self._sync_sprite(sprite)

        self._check_on_ground()
        self._check_goals()
        self._check_ball_stuck(delta_time)
        self._update_powerup(delta_time)

        self.time_remaining_ms -= delta_time
        if self.time_remaining_ms <= 0:
            self.time_remaining_ms = 0
            self._start_exit_transition()

    # --- RENDER ---
    def _render_field_fg(self, screen):
        pass

    def _render_shadows(self, screen):
        SHADOW_COLOR    = (0, 0, 0, 110)
        SHADOW_W_RATIO  = 0.80
        SHADOW_H_BASE   = 11
        SHADOW_Y_OFFSET = -3

        shadow_y = self.ground_y - SHADOW_Y_OFFSET

        candidates = list(self.shadow_sprites)
        boss = getattr(self, 'boss', None)
        if boss is not None and boss not in candidates:
            candidates.append(boss)

        for sprite in candidates:
            if not getattr(sprite, 'body', None):
                continue

            cx = sprite.rect.centerx
            sw = max(2, int(sprite.rect.width * SHADOW_W_RATIO))
            sh = max(1, SHADOW_H_BASE)

            shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, SHADOW_COLOR, (0, 0, sw, sh))
            screen.blit(shadow_surf, (cx - sw // 2, shadow_y - sh // 2))

    def render(self, screen):
        
        

        
        self._render_field(screen)
        self._render_shadows(screen)
        self.grupo_sprites.draw(screen)
        self._render_field_fg(screen)

        if not self.is_exiting:
            self._draw_hud(screen)
            self._render_powerup_hud(screen)
            if self.goal_scored:
                self._draw_goal_text(screen)

            if self.waiting_for_intro and self.fade_alpha <= 0:
                self._draw_intro_countdown(screen)

        if self.match_over and not (self.is_exiting and self.fade_alpha >= 255):
            text_surf = None
            text_color = Colors.WHITE

            if self.end_phase == "fin":
                text_surf = self.font_goal.render("FIN DEL PARTIDO", True, Colors.WHITE)
            elif self.end_phase == "result":
                text_surf = self.font_goal.render(self.result_text, True, self.result_color)

            if text_surf is not None:
                text_rect = text_surf.get_rect(center=(SW // 2, SH // 2))
                screen.blit(text_surf, text_rect)

        self.draw_fade(screen)

        renderer = PhysicsDebugRenderer(surface=screen, test=self, world=self.world)
        self.world.renderer = renderer
        if self.PHYSICS_DEBUG_MODE:
            renderer.render()
            for body in self.world.bodies:
                print(body)
                for fixture in body.fixtures:
                    print(fixture.shape)

    def _draw_intro_countdown(self, screen):
        seconds = self.intro_countdown_timer / 1000.0
        if seconds > 2:
            txt = "3"
        elif seconds > 1:
            txt = "2"
        elif seconds > 0:
            txt = "1"
        else:
            txt = "YA"

        surf_shadow = self.font_goal.render(txt, True, Colors.BLACK)
        surf_text = self.font_goal.render(txt, True, Colors.YELLOW)

        rect = surf_text.get_rect(center=(SW // 2, SH // 2))
        screen.blit(surf_shadow, (rect.x + 4, rect.y + 4))
        screen.blit(surf_text, rect)

    def _draw_hud(self, screen):
        surf = self.font_score.render(
            f"{self.score_left}  -  {self.score_right}", True, Colors.WHITE
        )
        screen.blit(surf, surf.get_rect(centerx=SW // 2, top=12))

        secs = max(0, self.time_remaining_ms // 1000)
        m, s = divmod(secs, 60)
        color = Colors.LIGHT_RED if secs <= 15 else Colors.WHITE
        tsurf = self.font_timer.render(f"{m}:{s:02d}", True, color)
        screen.blit(tsurf, tsurf.get_rect(centerx=SW // 2, top=66))

    def _draw_goal_text(self, screen):
        shadow = self.font_goal.render("GOL!", True, Colors.BLACK)
        text = self.font_goal.render("GOL!", True, Colors.YELLOW)
        cx, cy = SW // 2, SH // 2
        screen.blit(shadow, shadow.get_rect(center=(cx + 3, cy + 3)))
        screen.blit(text, text.get_rect(center=(cx, cy)))

    def _start_exit_transition(self):
        """Inicia secuencia de salida: FIN DEL PARTIDO -> RESULTADO -> fade."""
        if self.is_exiting:
            return

        self.is_exiting = True
        self.match_over = True

        if self.score_left > self.score_right:
            self.result_text = "VICTORY ROYALE"
            self.result_color = Colors.YELLOW
        else:
            self.result_text = "GAME OVER"
            self.result_color = Colors.LIGHT_RED

        self.end_phase = "fin"
        self.end_phase_timer_ms = 4000
        self.fade_started = False

    def _set_wait_timer(self):
        """Activa el tiempo de espera en negro antes de cambiar de escena."""
        self.wait_timer = 2.0

    def _execute_scene_jump(self):
        """Logica final de salto de escena (Campana o Arcade)."""
        if self.director.in_campaign:
            if self.score_left > self.score_right:
                self.director.advance_campaign()
            else:
                self.director.fail_campaign()
        else:
            player_won = self.score_left > self.score_right
            result = "winner_1" if player_won else ("tie" if self.score_left == self.score_right else "winner_2")
            self.director.cambiarEscena(EndScene(self.director, result))