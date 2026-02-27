import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
from ingame_menu_scene import IngameMenu
from end_scene import EndScene
from assets_manager import SFXAssets
from settings import ScreenSettings, GUISettings, Colors, GameSettings, VolumeController
from pygame.locals import *

# ── Física Box2D ─────────────────────────────────────────
PPM       = 10.0
TIME_STEP = 1.0 / 60.0
VEL_ITERS = 8
POS_ITERS = 3

def px2m(px): return px / PPM
def m2px(m):  return m  * PPM

# Pantalla y Posiciones
SW       = ScreenSettings.SCREEN_WIDTH   # 800
SH       = ScreenSettings.SCREEN_HEIGHT  # 600
GROUND_Y = 520                           # píxeles

# Portería
GOAL_W     = 80
GOAL_H     = 140
GOAL_POST  = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H

# Posiciones iniciales
PLAYER_START = (200, GROUND_Y - 60)
BALL_START   = (SW // 2, GROUND_Y - 220)

# Hitbox del jugador
PLAYER_HW = 7.0
PLAYER_HH = 3.5

# Movimiento
PLAYER_SPEED = 12.0
PLAYER_JUMP  = -18.0
GROUND_BLEND = 0.35
AIR_BLEND    = 0.12

# Gravedad
GRAVITY = (0, 35)

# Colores
BG_COLOR       = (30, 120, 60)
GROUND_COLOR   = (20, 100, 50)
GOAL_COLOR     = (255, 255, 255)
GOAL_NET_COLOR = (180, 180, 180, 80)
MUD_COLOR      = (90, 60, 30) # Color para el lodo

# Pausa tras gol
GOAL_PAUSE_MS = 2000

# ── Funciones de soporte originales ───────────────────────

def create_boundaries(world):
    # Suelo
    g = world.CreateStaticBody(position=(px2m(SW / 2), px2m(GROUND_Y)))
    g.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.6)
    # Techo
    c = world.CreateStaticBody(position=(px2m(SW / 2), px2m(-5)))
    c.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.2)
    # Paredes laterales
    wl = world.CreateStaticBody(position=(px2m(-5), px2m(GOAL_TOP_Y / 2)))
    wl.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)
    wr = world.CreateStaticBody(position=(px2m(SW + 5), px2m(GOAL_TOP_Y / 2)))
    wr.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

def create_goal_bodies(world, side):
    gx = 0 if side == 'left' else SW - GOAL_W
    cx = px2m(gx + GOAL_W / 2)
    bar = world.CreateStaticBody(position=(cx, px2m(GOAL_TOP_Y - GOAL_POST / 2)))
    bar.CreatePolygonFixture(box=(px2m(GOAL_W / 2), px2m(GOAL_POST / 2)), friction=0.3, restitution=0.4)
    px_post = (gx - GOAL_POST / 2) if side == 'left' else (gx + GOAL_W + GOAL_POST / 2)
    back = world.CreateStaticBody(position=(px2m(px_post), px2m(GOAL_TOP_Y + GOAL_H / 2)))
    back.CreatePolygonFixture(box=(px2m(GOAL_POST / 2), px2m(GOAL_H / 2)), friction=0.3, restitution=0.4)
    floor = world.CreateStaticBody(position=(cx, px2m(GROUND_Y)))
    floor.CreatePolygonFixture(box=(px2m(GOAL_W / 2), px2m(5)), friction=0.6)
    return pygame.Rect(gx, GOAL_TOP_Y, GOAL_W, GOAL_H)


class FirstScene(PyGameScene):

    def __init__(self, director):
        super().__init__(director)

        # Mundo Box2D
        self.world = Box2D.b2World(gravity=GRAVITY, doSleep=True)
        create_boundaries(self.world)

        # Porterías
        self.goal_l_rect = create_goal_bodies(self.world, 'left')
        self.goal_r_rect = create_goal_bodies(self.world, 'right')

        # ── NUEVOS ELEMENTOS: Bulldozer y Barro ──
        # Jefe Bulldozer con IA
        self.boss = RocketFactory.create_element("boss", self.world, (650, GROUND_Y - 60), "bulldozer")
        
        # Zonas de barro (Sensores)
        # Asegúrate de haber añadido RocketFactory.create_mud en factory.py
        self.lodos_fisicos = [
            RocketFactory.create_mud(self.world, (350, GROUND_Y - 5)),
            RocketFactory.create_mud(self.world, (550, GROUND_Y - 5))
        ]

        # Jugador y Pelota
        self.jugador = RocketFactory.create_element("player", self.world, PLAYER_START)
        self.pelota  = RocketFactory.create_element("ball",   self.world, BALL_START)

        # Grupo de sprites (Añadimos al boss)
        self.grupo_sprites = pygame.sprite.Group(self.jugador, self.pelota, self.boss)

        # Estado del juego
        self.move_left_flag  = False
        self.move_right_flag = False
        self.score_left  = 0
        self.score_right = 0
        self.time_remaining_ms = GameSettings.MATCH_DURATION * 1000
        self.match_over = False
        self.goal_scored = False
        self.goal_pause_timer = 0

        # Fuentes
        self.font_score = pygame.font.SysFont(GUISettings.FONT_TEXT, 48, bold=True)
        self.font_timer = pygame.font.SysFont(GUISettings.FONT_TEXT, 28)
        self.font_goal  = pygame.font.SysFont(GUISettings.FONT_TEXT, 72, bold=True)

    # ── MÉTODOS DE SOPORTE ──

    def _body_px(self, body):
        return (m2px(body.position.x), m2px(body.position.y))

    def _sync_sprite(self, sprite):
        if sprite.body:
            pos = sprite.body.position
            sprite.establecerPosicion((m2px(pos.x), m2px(pos.y)))

    def _check_on_ground(self):
        if not self.jugador.body: return
        bottom_m = self.jugador.body.position.y + PLAYER_HH
        ground_m = px2m(GROUND_Y)
        self.jugador.on_ground = bottom_m >= ground_m - 1.0

    def _apply_player_movement(self):
        if not self.jugador.body: return
        vel = self.jugador.body.linearVelocity
        target_vx = 0.0
        if self.move_left_flag:  target_vx = -PLAYER_SPEED
        if self.move_right_flag: target_vx =  PLAYER_SPEED
        blend  = GROUND_BLEND if self.jugador.on_ground else AIR_BLEND
        new_vx = vel.x + (target_vx - vel.x) * blend
        self.jugador.body.linearVelocity = (new_vx, vel.y)

    # ── LÓGICA IA BULLDOZER ──

    def _update_boss_ai(self):
        #El Bulldozer persigue el balón para estorbar al jugador.#
        if self.boss.body and self.pelota.body:
            target_x = self.pelota.body.position.x
            boss_x = self.boss.body.position.x
            
            # Se mueve hacia la posición X del balón
            if target_x < boss_x - 1.0:
                self.boss.move_left()
            elif target_x > boss_x + 1.0:
                self.boss.move_right()
            else:
                self.boss.stop_horizontal()

    # ── LÓGICA DE BARRO (EFECTO LODO) ──

    def _check_mud_effect(self):
        #Frena al jugador si pisa el lodo (usando los sensores de factory.py).
        for contact in self.world.contacts:
            if contact.touching:
                dataA = contact.fixtureA.body.userData
                dataB = contact.fixtureB.body.userData
                if (dataA == {'type': 'mud'}) or (dataB == {'type': 'mud'}):
                    # Reducimos drásticamente la velocidad horizontal
                    vel = self.jugador.body.linearVelocity
                    self.jugador.body.linearVelocity = (vel.x * 0.4, vel.y)

    # ── EVENTOS Y UPDATE ──

    def events(self, event_list):
        for ev in event_list:
            if ev.type == QUIT: self.director.salirPrograma()
            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    self.director.apilarEscena(IngameMenu(self.director))
                elif not self.goal_scored:
                    if ev.key in (K_a, K_LEFT):   self.move_left_flag = True
                    elif ev.key in (K_d, K_RIGHT): self.move_right_flag = True
                    elif ev.key in (K_w, K_UP, K_SPACE):
                        if self.jugador.on_ground:
                            self.jugador.body.linearVelocity = (self.jugador.body.linearVelocity.x, PLAYER_JUMP)
            elif ev.type == KEYUP:
                if ev.key in (K_a, K_LEFT):   self.move_left_flag = False
                elif ev.key in (K_d, K_RIGHT): self.move_right_flag = False

    def update(self, delta_time):
        if self.match_over: return

        if self.goal_scored:
            self.goal_pause_timer -= delta_time
            if self.goal_pause_timer <= 0:
                self.goal_scored = False
                self._reset_positions()
            return

        # Movimiento Player e IA Boss
        self._apply_player_movement()
        self._update_boss_ai()
        if hasattr(self.boss, 'update_logic'): # Gestión del cabreo (Ultimate)
            self.boss.update_logic(delta_time)

        # Física
        self.world.Step(TIME_STEP, VEL_ITERS, POS_ITERS)
        self.world.ClearForces()

        # Sincronización
        dt = delta_time / 1000.0
        for sprite in self.grupo_sprites:
            self._sync_sprite(sprite)
            sprite.update(dt)

        self._check_on_ground()
        self._check_mud_effect()
        self._check_goals()

        self.time_remaining_ms -= delta_time
        if self.time_remaining_ms <= 0:
            self._finish_match()

    def _on_goal(self):
        self.goal_scored = True
        self.goal_pause_timer = GOAL_PAUSE_MS
        try:
            sound = SFXAssets.goal1.play()
            sound.set_volume(VolumeController.get_current_volume())
        except: pass

    def _reset_positions(self):
        self.jugador.body.position = (px2m(PLAYER_START[0]), px2m(PLAYER_START[1]))
        self.jugador.body.linearVelocity = (0, 0)
        self.pelota.body.position = (px2m(BALL_START[0]), px2m(BALL_START[1]))
        self.pelota.body.linearVelocity = (0, 0)
        self.move_left_flag = self.move_right_flag = False

    def _check_goals(self):
        if self.goal_scored: return
        bx, by = self._body_px(self.pelota.body)
        if self.goal_l_rect.collidepoint(bx, by):
            self.score_right += 1
            self._on_goal()
        elif self.goal_r_rect.collidepoint(bx, by):
            self.score_left += 1
            self._on_goal()

    def _finish_match(self):
        self.time_remaining_ms = 0
        self.match_over = True
        if self.score_left > self.score_right: result = "winner_1"
        elif self.score_right > self.score_left: result = "winner_2"
        else: result = "tie"
        self.director.apilarEscena(EndScene(self.director, result=result))

    # ── RENDER ──

    def render(self, screen):
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, SW, SH - GROUND_Y))

        # Dibujar barro (Capas bajas)
        for lodo in self.lodos_fisicos:
            pos = lodo.position
            rect = pygame.Rect(0, 0, 100, 25)
            rect.center = (m2px(pos.x), m2px(pos.y))
            pygame.draw.ellipse(screen, MUD_COLOR, rect)

        # Decoración campo
        pygame.draw.line(screen, (255, 255, 255), (SW // 2, 0), (SW // 2, GROUND_Y), 1)
        pygame.draw.circle(screen, (255, 255, 255), (SW // 2, GROUND_Y - 120), 60, 1)

        # Porterías y Sprites
        self._draw_goal(screen, 'left')
        self._draw_goal(screen, 'right')
        self.grupo_sprites.draw(screen)

        # HUD
        self._draw_hud(screen)
        if self.goal_scored: self._draw_goal_text(screen)

    def _draw_goal(self, screen, side):
        gx = 0 if side == 'left' else SW - GOAL_W
        net = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
        net.fill(GOAL_NET_COLOR)
        for i in range(0, GOAL_W, 10): pygame.draw.line(net, (200, 200, 200, 40), (i, 0), (i, GOAL_H), 1)
        for j in range(0, GOAL_H, 10): pygame.draw.line(net, (200, 200, 200, 40), (0, j), (GOAL_W, j), 1)
        screen.blit(net, (gx, GOAL_TOP_Y))
        pygame.draw.rect(screen, GOAL_COLOR, (gx, GOAL_TOP_Y - GOAL_POST, GOAL_W, GOAL_POST))
        px = gx if side == 'left' else gx + GOAL_W - GOAL_POST
        pygame.draw.rect(screen, GOAL_COLOR, (px, GOAL_TOP_Y - GOAL_POST, GOAL_POST, GOAL_H + GOAL_POST))

    def _draw_hud(self, screen):
        surf = self.font_score.render(f"{self.score_left}  -  {self.score_right}", True, Colors.WHITE)
        screen.blit(surf, surf.get_rect(centerx=SW // 2, top=12))
        secs = max(0, self.time_remaining_ms // 1000); m, s = divmod(secs, 60)
        color = Colors.LIGHT_RED if secs <= 15 else Colors.WHITE
        tsurf = self.font_timer.render(f"{m}:{s:02d}", True, color)
        screen.blit(tsurf, tsurf.get_rect(centerx=SW // 2, top=66))

    def _draw_goal_text(self, screen):
        shadow = self.font_goal.render("¡GOL!", True, Colors.BLACK)
        text   = self.font_goal.render("¡GOL!", True, Colors.YELLOW)
        screen.blit(shadow, shadow.get_rect(center=(SW // 2 + 3, SH // 2 + 3)))
        screen.blit(text,   text.get_rect(center=(SW // 2, SH // 2)))