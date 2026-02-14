"""Main menu scene.

Provides the primary menu interface with options to:
- Start campaign mode
- Open settings
- Exit the game
"""

import pygame
from features.match.scene import MatchScene
from features.settings.scene import SettingsScene
from features.common.scene import PyGameScene
from features.menu.ui.screens import InitialGUIScreen
from pygame.locals import KEYDOWN, K_ESCAPE, QUIT


class Menu(PyGameScene):
    """Main menu scene.

    Displays the game's main menu with buttons for:
    - Starting campaign mode
    - Accessing settings
    - Exiting the game

    Attributes:
        screenList: List of GUI screens (currently only has initial screen)
        currentScreen: Index of the currently active screen
    """

    def __init__(self, director):
        """Initialize the main menu.

        Args:
            director: Game director instance
        """
        PyGameScene.__init__(self, director)
        self.screenList = []

        self.screenList.append(InitialGUIScreen(self))
        self.showInitialScreen()

    def update(self, *args):
        """Update menu state (currently no update logic needed)."""
        return

    def events(self, event_list):
        """Handle input events.

        Args:
            event_list: List of pygame events
        """
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.exit()
            elif event.type == QUIT:
                self.director.exitScene()
        # Pass events to the current GUI screen
        self.screenList[self.currentScreen].events(event_list)

    def render(self, screen):
        """Render the current menu screen.

        Args:
            screen: pygame.Surface to render on
        """
        self.screenList[self.currentScreen].render(screen)

    def exit(self):
        """Exit the menu and close the game."""
        self.director.exitScene()

    def playCampaign(self):
        """Start campaign mode by launching the match scene."""
        campaignScene = MatchScene(self.director)
        self.director.appendScene(campaignScene)
        self.currentScreen = len(self.screenList) - 1

    def showInitialScreen(self):
        """Display the initial/main menu screen."""
        self.currentScreen = 0

    def showSettingsScreen(self):
        """Open the settings screen."""
        settingsScreen = SettingsScene(self.director)
        self.director.appendScene(settingsScreen)
        self.currentScreen = len(self.screenList) - 1
