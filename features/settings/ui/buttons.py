"""
Buttons for the settings screen
"""

from assets.gui_elements import Button
from settings import ScreenSettings
from features.settings.constants import SAVE_BUTTON_Y


class SaveButton(Button):
    """Button to save current settings"""

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(ScreenSettings.SCREEN_WIDTH // 2, SAVE_BUTTON_Y),
            text="Save Settings",
        )
        # Center the button
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        """Called when button is clicked - delegates to the scene"""
        # self.screen is the SettingsScene instance
        self.screen.save_settings()
