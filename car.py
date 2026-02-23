import pygame
from pygame.locals import *
from settings import ScreenSettings

# Default stats (la física la gestiona Box2D, estos son para factory.py)
DEFAULT_STATS = {
    'move_speed': 5.0,
    'jump_force': 80.0,
    'mass': 1.0,
    'scale': 1.0,
}

BOSS1_STATS = {
    'move_speed': 10.0,
    'jump_force': 70.0,
    'mass': 0.8,
    'scale': 0.9,
}

BOSS2_STATS = {
    'move_speed': 3.0,
    'jump_force': 100.0,
    'mass': 3.0,
    'scale': 1.8,
}

BOSS3_STATS = {
    'move_speed': 6.0,
    'jump_force': 120.0,
    'mass': 1.0,
    'scale': 1.0,
}

# Asset paths
PLAYER_CAR_IMG = './assets/cars/player_car.png'
BOSS_CAR_IMG   = './assets/cars/placeholder_car.png'
WHEEL_IMG      = './assets/cars/car_wheel.png'

# Wheel offsets como proporción del cuerpo (0.0 a 1.0)
WHEEL_OFFSET_LEFT_X  = 0.06
WHEEL_OFFSET_LEFT_Y  = 0.70
WHEEL_OFFSET_RIGHT_X = 0.69
WHEEL_OFFSET_RIGHT_Y = 0.70


class MySprite(pygame.sprite.Sprite):

    def __init__(self, body_path, carPos=(0, 0), scale=1.0):
        super().__init__()

        # Cargar cuerpo
        try:
            body = pygame.image.load(body_path).convert_alpha()
        except:
            body = pygame.Surface((80, 50), pygame.SRCALPHA)
            body.fill((200, 50, 50))

        # Cargar rueda
        try:
            wheel = pygame.image.load(WHEEL_IMG).convert_alpha()
            wheel_w = int(wheel.get_width() * scale)
            wheel_h = int(wheel.get_height() * scale)
            self.wheel_img = pygame.transform.scale(wheel, (wheel_w, wheel_h))
        except:
            self.wheel_img = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(self.wheel_img, (50, 50, 50), (10, 10), 10)

        # Escalar cuerpo
        w = int(body.get_width() * scale)
        h = int(body.get_height() * scale)
        self.body_img = pygame.transform.scale(body, (w, h))

        # Offsets proporcionales
        left_x  = int(w * WHEEL_OFFSET_LEFT_X)
        left_y  = int(h * WHEEL_OFFSET_LEFT_Y)
        right_x = int(w * WHEEL_OFFSET_RIGHT_X)
        right_y = int(h * WHEEL_OFFSET_RIGHT_Y)

        # Superficie combinada (cuerpo + ruedas)
        total_h = h + self.wheel_img.get_height() // 2
        self.image = pygame.Surface((w, total_h), pygame.SRCALPHA)
        self.image.blit(self.body_img, (0, 0))
        self.image.blit(self.wheel_img, (left_x,  left_y))
        self.image.blit(self.wheel_img, (right_x, right_y))

        self.rect = self.image.get_rect()
        self.establecerPosicion(carPos)

        # Box2D body (asignado por factory.py)
        self.body = None

    def establecerPosicion(self, pos):
        """Sincroniza el sprite con la posición central de Box2D."""
        self.rect.centerx = int(pos[0])
        self.rect.centery = int(pos[1])

    def update(self, dt):
        pass

    def render(self, screen):
        screen.blit(self.image, self.rect)


class Car(MySprite):

    def __init__(self, body_path, carPos=(0, 0), stats=None):
        if stats is None:
            stats = DEFAULT_STATS

        super().__init__(body_path, carPos, scale=stats.get('scale', 1.0))

        self.move_speed = stats.get('move_speed', DEFAULT_STATS['move_speed'])
        self.jump_force = stats.get('jump_force', DEFAULT_STATS['jump_force'])
        self.mass       = stats.get('mass',       DEFAULT_STATS['mass'])
        self.on_ground  = False

    def jump(self):
        if self.on_ground and self.body:
            self.body.ApplyLinearImpulse(
                impulse=(0, -self.jump_force),
                point=self.body.worldCenter,
                wake=True
            )

    def move_left(self):
        if self.body:
            self.body.ApplyForce(
                force=(-self.move_speed * 10, 0),
                point=self.body.worldCenter,
                wake=True
            )

    def move_right(self):
        if self.body:
            self.body.ApplyForce(
                force=(self.move_speed * 10, 0),
                point=self.body.worldCenter,
                wake=True
            )

    def stop_horizontal(self):
        if self.body:
            vel = self.body.linearVelocity
            self.body.linearVelocity = (vel.x * 0.8, vel.y)

    def update(self, dt):
        pass


class PlayerCar(Car):

    def __init__(self, carPos=(100, 100)):
        super().__init__(PLAYER_CAR_IMG, carPos, stats=DEFAULT_STATS)
        self.moving_left  = False
        self.moving_right = False

    def handle_input(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_a:
                    self.moving_left = True
                elif event.key == K_d:
                    self.moving_right = True
                elif event.key == K_w:
                    self.jump()
            elif event.type == KEYUP:
                if event.key == K_a:
                    self.moving_left = False
                elif event.key == K_d:
                    self.moving_right = False

        if self.moving_left:
            self.move_left()
        elif self.moving_right:
            self.move_right()
        else:
            self.stop_horizontal()

    def update(self, dt):
        super().update(dt)


class BossCar(Car):

    def __init__(self, carPos=(0, 0), stats=None):
        if stats is None:
            stats = DEFAULT_STATS
        super().__init__(BOSS_CAR_IMG, carPos, stats)

    def update(self, dt):
        super().update(dt)


class Bulldozer(BossCar):
    def __init__(self, carPos=(0, 0)):
        super().__init__(carPos, stats=BOSS1_STATS)


class MotoMoto(BossCar):
    def __init__(self, carPos=(0, 0)):
        super().__init__(carPos, stats=BOSS2_STATS)


class LaJenny(BossCar):
    def __init__(self, carPos=(0, 0)):
        super().__init__(carPos, stats=BOSS3_STATS)