import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
from settings import ScreenSettings
from pygame.locals import *

class MatchScene(PyGameScene):
    def __init__(self, director):
        super().__init__(director)
        self.world = Box2D.b2World(gravity=(0, 15), doSleep=True)

        # Spawns: Jugador y Balón centrado
        self.jugador = RocketFactory.create_element("player", self.world, (150, 500))
        self.pelota  = RocketFactory.create_element("ball", self.world, (ScreenSettings.SCREEN_WIDTH // 2, 300))

        # Límites del estadio con EdgeFixtures
        self.estadio = self.world.CreateStaticBody(position=(0, 0))
        w, h = 80, 60
        self.estadio.CreateEdgeFixture(vertices=[(1, h-1), (w-1, h-1)], friction=0.5) # Suelo
        self.estadio.CreateEdgeFixture(vertices=[(1, 1), (w-1, 1)], friction=0.5)     # Techo
        self.estadio.CreateEdgeFixture(vertices=[(1, 1), (1, h-1)], friction=0.5)     # Pared Izq
        self.estadio.CreateEdgeFixture(vertices=[(w-1, 1), (w-1, h-1)], friction=0.5) # Pared Der

        self.grupo_sprites = pygame.sprite.Group(self.jugador, self.pelota)

    def update(self, delta_time):
        self.world.Step(delta_time / 1000.0, 8, 3)
        for sprite in self.grupo_sprites:
            pos = sprite.body.position
            sprite.establecerPosicion((pos.x * 10, pos.y * 10))
            sprite.update(delta_time)
            if sprite == self.jugador:
                sprite.on_ground = abs(sprite.body.linearVelocity.y) < 0.2

    def events(self, event_list):
        self.jugador.handle_input(event_list)
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE: self.director.exitScene()

    def render(self, screen):
        screen.fill((20, 20, 25))
        self.grupo_sprites.draw(screen)