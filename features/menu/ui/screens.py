"""
GUI screens for the menu feature
"""

from assets.gui_elements import GUIScreen
from assets.assets_manager import GUIAssets
from features.menu.ui.buttons import PlayButton, SettingsButton, ExitButton


class InitialGUIScreen(GUIScreen):
    """Main menu initial screen with play, settings, and exit buttons"""

    def __init__(self, menu):
        GUIScreen.__init__(self, menu, GUIAssets.main_menu_bg)

        # Create buttons
        playButton = PlayButton(self)
        exitButton = ExitButton(self)
        settingsButton = SettingsButton(self)

        # Add to GUI elements
        self.GUIElements.append(playButton)
        self.GUIElements.append(exitButton)
        self.GUIElements.append(settingsButton)
