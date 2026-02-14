"""
Buttons for the ingame pause menu
"""

from assets.gui_elements import Button
from settings import ScreenSettings


class ResumeButton(Button):
    """Button to resume the game"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH // 2,
                ScreenSettings.SCREEN_HEIGHT // 2 - 50,
            ),
            text="Resume Game",
        )
        # Center the button
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        """Resume the game with countdown"""
        self.screen.menu.resumeGame()


class SettingsButton(Button):
    """Button to open settings from pause menu"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH // 2,
                ScreenSettings.SCREEN_HEIGHT // 2 + 20,
            ),
            text="Settings",
        )
        # Center the button
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        """Open settings screen"""
        self.screen.menu.showSettings()


class ExitToMenuButton(Button):
    """Button to exit to main menu"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH // 2,
                ScreenSettings.SCREEN_HEIGHT // 2 + 90,
            ),
            text="Exit to Main Menu",
        )
        # Center the button
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        """Exit to main menu"""
        self.screen.menu.exitToMainMenu()
