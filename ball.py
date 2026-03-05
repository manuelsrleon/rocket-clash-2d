import pygame

# Asset path
BALL_IMG = './assets/balls/ball.png'

class Ball(pygame.sprite.Sprite):
    def __init__(self, ballPos=(400, 300), scale=0.8): # Escala reducida para que no sea gigante
        super().__init__()

        # Cargar imagen
        try:
            img = pygame.image.load(BALL_IMG).convert_alpha()
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            self.image = pygame.transform.scale(img, (w, h))
        except:
            # Placeholder circular si falla la carga
            size = int(40 * scale)
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 255, 255), (size // 8, size // 8), size // 8)

        self.rect = self.image.get_rect()
        self.establecerPosicion(ballPos)

        # Box2D body (asignado por factory.py)
        self.body = None
        self.angle = 0.0
        self.original_image = self.image.copy()

    def establecerPosicion(self, pos):
        """Sincroniza el sprite con la posición de Box2D."""
        self.rect.centerx = int(pos[0])
        self.rect.centery = int(pos[1])

    def update(self, dt):
        """Actualiza la rotación visual según la velocidad angular de Box2D."""
        if self.body:
            self.angle -= self.body.angularVelocity
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

    def render(self, screen):
        screen.blit(self.image, self.rect)