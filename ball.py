import pygame

# Asset path
BALL_IMG = './assets/balls/ball.png'

# Escala Box2D → píxeles (misma que factory.py)
PHYSICS_SCALE = 10.0


class Ball(pygame.sprite.Sprite):

    def __init__(self, ballPos=(400, 300), scale=1.0):
        super().__init__()

        # Cargar imagen
        try:
            img = pygame.image.load(BALL_IMG).convert_alpha()
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            self.image = pygame.transform.scale(img, (w, h))
        except:
            # Placeholder circular
            size = int(40 * scale)
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(
                self.image,
                (255, 255, 255),
                (size // 2, size // 2),
                size // 2
            )

        self.rect = self.image.get_rect()
        self.establecerPosicion(ballPos)

        # Box2D body (asignado por factory.py)
        self.body = None

        # Ángulo de rotación visual
        self.angle = 0.0
        self.original_image = self.image.copy()

    def establecerPosicion(self, pos):
        """Sincroniza el sprite con la posición de Box2D."""
        self.rect.centerx = int(pos[0])
        self.rect.centery = int(pos[1])

    def update(self, dt):
        """Actualiza la rotación visual según la velocidad angular de Box2D."""
        if self.body:
            # Rotar imagen según velocidad angular del cuerpo
            self.angle -= self.body.angularVelocity
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            # Mantener el centro al rotar
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

    def render(self, screen):
        screen.blit(self.image, self.rect)