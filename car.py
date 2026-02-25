import pygame
from pygame.locals import *
from settings import ScreenSettings

# Estadísticas base para la física
DEFAULT_STATS = {'move_speed': 5.0, 'jump_force': 80.0, 'mass': 1.0, 'scale': 1.0}
BOSS1_STATS = {'move_speed': 10.0, 'jump_force': 70.0, 'mass': 0.8, 'scale': 0.9}

PLAYER_CAR_IMG = './assets/cars/player_car.png'
WHEEL_IMG      = './assets/cars/car_wheel.png'

class MySprite(pygame.sprite.Sprite):
    def __init__(self, body_path, carPos=(0, 0), scale=1.0):
        super().__init__()
        try:
            body = pygame.image.load(body_path).convert_alpha()
        except:
            body = pygame.Surface((80, 50), pygame.SRCALPHA)
            body.fill((200, 50, 50))
        
        w, h = int(body.get_width() * scale), int(body.get_height() * scale)
        self.image = pygame.transform.scale(body, (w, h))
        self.rect = self.image.get_rect()
        self.establecerPosicion(carPos)
        self.body = None

    def establecerPosicion(self, pos):
        self.rect.centerx, self.rect.centery = int(pos[0]), int(pos[1])

class Car(MySprite):
    def __init__(self, body_path, carPos=(0, 0), stats=None):
        stats = stats or DEFAULT_STATS
        super().__init__(body_path, carPos, scale=stats.get('scale', 1.0))
        self.move_speed = stats.get('move_speed', DEFAULT_STATS['move_speed'])
        self.jump_force = stats.get('jump_force', DEFAULT_STATS['jump_force'])
        self.mass = stats.get('mass', DEFAULT_STATS['mass'])
        self.on_ground = False

    def jump(self):
        if self.on_ground and self.body:
            self.body.ApplyLinearImpulse(impulse=(0, -self.jump_force), point=self.body.worldCenter, wake=True)

    def move_left(self):
        if self.body: self.body.ApplyForce(force=(-self.move_speed * 10, 0), point=self.body.worldCenter, wake=True)

    def move_right(self):
        if self.body: self.body.ApplyForce(force=(self.move_speed * 10, 0), point=self.body.worldCenter, wake=True)

    def stop_horizontal(self):
        if self.body:
            vel = self.body.linearVelocity
            self.body.linearVelocity = (vel.x * 0.8, vel.y)

class PlayerCar(Car):
    def __init__(self, carPos=(100, 100)):
        super().__init__(PLAYER_CAR_IMG, carPos, stats=DEFAULT_STATS)
        self.moving_left = self.moving_right = False

    def handle_input(self, event_list):
        keys = pygame.key.get_pressed()
        self.moving_left = keys[K_a]
        self.moving_right = keys[K_d]
        
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_w:
                self.jump()

        if self.moving_left: self.move_left()
        elif self.moving_right: self.move_right()
        else: self.stop_horizontal()