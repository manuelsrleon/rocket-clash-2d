import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
from settings import ScreenSettings, GUISettings, Colors, GameSettings
from pygame.locals import *

class MatchScene(PyGameScene):
    def __init__(self, director):
        super().__init__(director)

        self.world = Box2D.b2World(gravity=(0, 10), doSleep=True)

        # Suelo estático
        self.ground = self.world.CreateStaticBody(position=(0, 55))
        self.ground.CreateEdgeFixture(vertices=[(0, 0), (80, 0)], friction=0.5)

        # Crear jugador y pelota via factoría
        self.jugador = RocketFactory.create_element("player", self.world, (100, 300))
        self.pelota  = RocketFactory.create_element("ball",   self.world, (400, 300))

        self.grupo_sprites = pygame.sprite.Group(self.jugador, self.pelota)

        # Timer
        pygame.font.init()
        self.timer_font = pygame.font.SysFont(GUISettings.FONT_TEXT, 48, bold=True)
        self.time_remaining_ms  = GameSettings.MATCH_DURATION * 1000
        self.match_over = False

    def update(self, delta_time):
        time_step = delta_time / 1000.0
        self.world.Step(time_step, 6, 2)

        # Sincronizar sprites con Box2D y llamar update
        for sprite in self.grupo_sprites:
            pos = sprite.body.position
            sprite.establecerPosicion((pos.x * 10, pos.y * 10))
            sprite.update(time_step)

        # Match timer
        if not self.match_over:
            self.time_remaining_ms -= delta_time
            if self.time_remaining_ms <= 0:
                self.time_remaining_ms = 0
                self.match_over = True
                #TODO: add end scene here

    def events(self, event_list):
        # Delegar input al PlayerCar
        self.jugador.handle_input(event_list)

        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.director.exitScene()

    def render(self, screen):
        screen.fill(Colors.BLACK)
        self.grupo_sprites.draw(screen)
        self._render_timer(screen)

    def _render_timer(self, screen):
        total_secs  = max(0, self.time_remaining_ms // 1000)
        minutes     = total_secs // 60
        seconds     = total_secs % 60
        timer_str   = f"{minutes:01d}:{seconds:02d}"

        #change color if time is running out (15 seconds or less)
        color = Colors.LIGHT_RED if total_secs <= 15 else Colors.WHITE
        surface = self.timer_font.render(timer_str, True, color)
        rect    = surface.get_rect(
            centerx=ScreenSettings.SCREEN_WIDTH // 2,
            top=16,
        )
        screen.blit(surface, rect)