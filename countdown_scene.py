import pygame
from scene import PyGameScene
from settings import ScreenSettings, GUISettings


# Countdown Constants
COUNTDOWN_START_VALUE = 3
COUNTDOWN_FONT_SIZE = 120
COUNTDOWN_COLOR = (255, 255, 255)
OVERLAY_ALPHA = 100
OVERLAY_COLOR = (0, 0, 0)


class CountdownScene(PyGameScene):
    def __init__(self, director):
        super().__init__(director)

        self.is_overlay = True

        self.countdown_value = COUNTDOWN_START_VALUE  # Starts at 3
        self.countdown_timer = 0  # Milliseconds accumulated

        self.overlay = pygame.Surface(
            (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)
        )
        self.overlay.set_alpha(OVERLAY_ALPHA)
        self.overlay.fill(OVERLAY_COLOR)

        pygame.font.init()
        self.countdown_font = pygame.font.SysFont(
            GUISettings.FONT_TEXT, COUNTDOWN_FONT_SIZE, bold=True
        )

    def update(self, delta_time):
        self.countdown_timer += delta_time

        if self.countdown_timer >= 1000:
            self.countdown_timer = 0
            self.countdown_value -= 1

            if self.countdown_value <= 0:
                self.director.exitScene()

    def events(self, event_list):
        pass

    def render(self, screen):
        # Draw semi-transparent overlay
        screen.blit(self.overlay, (0, 0))

        # Draw countdown number in the center
        countdown_text = self.countdown_font.render(
            str(self.countdown_value), True, COUNTDOWN_COLOR
        )
        countdown_rect = countdown_text.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT // 2)
        )
        screen.blit(countdown_text, countdown_rect)
