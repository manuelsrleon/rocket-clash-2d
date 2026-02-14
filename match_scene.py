import pygame
from scene import PyGameScene
from settings import ScreenSettings
from pygame.locals import KEYDOWN, K_ESCAPE
from ingame_menu_scene import IngameMenu


class MatchScene(PyGameScene):

    def __init__(self, director):
        super().__init__(director)
        # Ball properties
        self.ball_x = 100
        self.ball_y = ScreenSettings.SCREEN_HEIGHT // 2
        self.ball_radius = 20
        self.ball_color = (255, 255, 0)
        # Blinking properties
        self.blink_timer = 0
        self.ball_visible = True

    def update(self, delta_time):
        self.blink_timer += delta_time
        if self.blink_timer >= 1000:
            self.ball_visible = not self.ball_visible
            self.blink_timer = 0

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                # Open ingame menu instead of exiting directly
                ingame_menu = IngameMenu(self.director)
                self.director.apilarEscena(ingame_menu)

    def render(self, screen):
        screen.fill((0, 0, 0))

        # Draw blinking ball if visible
        if self.ball_visible:
            pygame.draw.circle(
                screen, self.ball_color, (self.ball_x, self.ball_y), self.ball_radius
            )

        # Draw instructions
        font = pygame.font.SysFont("Arial", 30)
        text = font.render(
            "Match Scene - Press ESC for menu", True, (255, 255, 255)
        )
        screen.blit(text, (20, ScreenSettings.SCREEN_HEIGHT / 2 - 100))
