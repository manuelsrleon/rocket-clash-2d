"""Match/gameplay scene.

This is a placeholder implementation showing:
- A blinking ball animation
- ESC key to open pause menu

Future implementation will include full Rocket League-style gameplay.
"""

from features.common.scene import PyGameScene
from features.common.ingame_menu.scene import IngameMenu
from settings import ScreenSettings
import pygame
from pygame.locals import KEYDOWN, K_ESCAPE


class MatchScene(PyGameScene):
    """Main gameplay scene (currently a placeholder).

    Features:
    - Blinking ball animation (demonstrates delta_time usage)
    - ESC to open pause menu
    - Black background

    Attributes:
        ball_x, ball_y: Ball position
        ball_radius: Ball size
        ball_color: Ball color (yellow)
        blink_timer: Milliseconds since last blink toggle
        ball_visible: Current visibility state
    """

    def __init__(self, director):
        """Initialize the match scene.

        Args:
            director: Game director instance
        """
        super().__init__(director)
        # Ball properties
        self.ball_x = 100  # Left side of screen
        self.ball_y = ScreenSettings.SCREEN_HEIGHT // 2
        self.ball_radius = 20
        self.ball_color = (255, 255, 0)  # Yellow
        # Blinking properties
        self.blink_timer = 0
        self.ball_visible = True

    def update(self, delta_time):
        """Update match state.

        Currently only handles ball blinking animation.

        Args:
            delta_time: Milliseconds since last frame
        """
        # Update blink timer (delta_time is in milliseconds)
        self.blink_timer += delta_time
        # Toggle visibility every 1000ms (1 second)
        if self.blink_timer >= 1000:
            self.ball_visible = not self.ball_visible
            self.blink_timer = 0

    def events(self, event_list):
        """Handle input events.

        Args:
            event_list: List of pygame events
        """
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                # Open ingame menu instead of exiting directly
                ingame_menu = IngameMenu(self.director)
                self.director.appendScene(ingame_menu)

    def render(self, screen):
        """Render the match scene.

        Args:
            screen: pygame.Surface to render on
        """
        screen.fill((0, 0, 0))  # Black background

        # Draw blinking ball if visible
        if self.ball_visible:
            pygame.draw.circle(
                screen, self.ball_color, (self.ball_x, self.ball_y), self.ball_radius
            )

        # Draw instructions
        text = pygame.font.SysFont("Arial", 30).render(
            "Match Scene - Press ESC for menu", True, (255, 255, 255)
        )
        screen.blit(text, (20, ScreenSettings.SCREEN_HEIGHT / 2 - 100))
