"""
GUI screens for the ingame pause menu
"""

from assets.gui_elements import GUIScreen
from features.common.ingame_menu.ui.buttons import (
    ResumeButton,
    SettingsButton,
    ExitToMenuButton,
)


class IngameMenuGUIScreen(GUIScreen):
    """Pause menu screen with resume, settings, and exit buttons"""

    def __init__(self, menu):
        GUIScreen.__init__(self, menu, image=None)

        # Create buttons
        resume_button = ResumeButton(self)
        settings_button = SettingsButton(self)
        exit_button = ExitToMenuButton(self)

        # Add buttons to the screen
        self.GUIElements.append(resume_button)
        self.GUIElements.append(settings_button)
        self.GUIElements.append(exit_button)
