"""
Buttons for the main menu screen
"""

from assets.gui_elements import Button
from settings import ScreenSettings


class PlayButton(Button):
    """Button to start campaign mode"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH - 200,
                ScreenSettings.SCREEN_HEIGHT - 222,
            ),
            text="Campaign Mode",
        )

    def action(self):
        """Start the campaign/match scene"""
        self.screen.menu.playCampaign()


class SettingsButton(Button):
    """Button to open settings"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH - 200,
                ScreenSettings.SCREEN_HEIGHT - 150,
            ),
            text="Settings",
        )

    def action(self):
        """Open settings screen"""
        self.screen.menu.showSettingsScreen()


class ExitButton(Button):
    """Button to exit the game"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH - 200,
                ScreenSettings.SCREEN_HEIGHT - 78,
            ),
            text="Exit",
        )

    def action(self):
        """Exit the game"""
        self.screen.menu.exit()
