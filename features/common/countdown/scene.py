"""Countdown overlay scene.

Displays a countdown (3-2-1) before resuming gameplay.
Automatically exits when the countdown reaches 0.

Used after unpausing the game to give the player time to prepare.
"""

import pygame
from features.common.scene import PyGameScene
from features.common.countdown.constants import (
    COUNTDOWN_START_VALUE,
    COUNTDOWN_FONT_SIZE,
    COUNTDOWN_COLOR,
    OVERLAY_ALPHA,
    OVERLAY_COLOR,
)
from settings import ScreenSettings, GUISettings


class CountdownScene(PyGameScene):
    """
    A countdown overlay scene that displays a countdown timer.
    When the countdown reaches 0, it automatically exits and returns to the previous scene.
    """

    def __init__(self, director):
        """Initialize the countdown scene.

        Args:
            director: Game director instance
        """
        super().__init__(director)

        # This scene should render over the previous scene
        self.render_over_previous = True

        # Mark as overlay so director knows to render scene below
        self.is_overlay = True

        # Countdown state
        self.countdown_value = COUNTDOWN_START_VALUE  # Starts at 3
        self.countdown_timer = 0  # Milliseconds accumulated

        # Create semi-transparent overlay surface
        self.overlay = pygame.Surface(
            (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)
        )
        self.overlay.set_alpha(OVERLAY_ALPHA)
        self.overlay.fill(OVERLAY_COLOR)

        # Initialize font for countdown display
        pygame.font.init()
        self.countdown_font = pygame.font.SysFont(
            GUISettings.FONT_TEXT, COUNTDOWN_FONT_SIZE, bold=True
        )

    def update(self, delta_time):
        """Update countdown timer.

        Decrements the countdown value every second.
        Automatically exits when reaching 0.

        Args:
            delta_time: Milliseconds since last frame
        """
        self.countdown_timer += delta_time

        # Every 1000ms (1 second), decrease countdown
        if self.countdown_timer >= 1000:
            self.countdown_timer = 0
            self.countdown_value -= 1

            # When countdown reaches 0, exit this scene
            if self.countdown_value <= 0:
                self.director.exitScene()

    def events(self, event_list):
        """Handle events (countdown doesn't process any input).

        The countdown runs automatically and cannot be interrupted.

        Args:
            event_list: List of pygame events (ignored)
        """
        pass

    def render(self, screen):
        """Render the countdown overlay.

        Displays:
        1. Semi-transparent overlay
        2. Large countdown number in center

        Args:
            screen: pygame.Surface to render on
        """
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
