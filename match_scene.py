import pygame
import Box2D
from scene import PyGameScene
from factory import RocketFactory
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

    def update(self, delta_time):
        time_step = delta_time / 1000.0
        self.world.Step(time_step, 6, 2)

        # Sincronizar sprites con Box2D y llamar update
        for sprite in self.grupo_sprites:
            pos = sprite.body.position
            sprite.establecerPosicion((pos.x * 10, pos.y * 10))
            sprite.update(time_step)

    def events(self, event_list):
        # Delegar input al PlayerCar
        self.jugador.handle_input(event_list)

        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.director.exitScene()

    def render(self, screen):
        screen.fill((20, 20, 25))
        self.grupo_sprites.draw(screen)