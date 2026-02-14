"""Ingame pause menu scene.

Provides a semi-transparent overlay menu during gameplay with options to:
- Resume the game (with countdown)
- Access settings
- Exit to main menu

This scene renders over the game scene using overlay mode.
"""

import pygame
from features.common.scene import PyGameScene
from features.common.ingame_menu.constants import (
    OVERLAY_ALPHA,
    OVERLAY_COLOR,
    MENU_WIDTH,
    MENU_HEIGHT,
    MENU_BG_COLOR,
    MENU_BORDER_COLOR,
    TITLE_COLOR,
)
from features.common.ingame_menu.ui.screens import IngameMenuGUIScreen
from settings import ScreenSettings, GUISettings
from features.settings.scene import SettingsScene
from features.common.countdown.scene import CountdownScene
from pygame.locals import KEYDOWN, K_ESCAPE


class IngameMenu(PyGameScene):
    """Pause menu overlay scene.

    This scene appears when the player presses ESC during gameplay.
    It displays a semi-transparent overlay with menu options.

    Features:
    - Semi-transparent black overlay (alpha 180/255)
    - Centered menu panel
    - Resume, Settings, and Exit buttons
    - ESC key to resume

    Attributes:
        is_overlay: True - renders over the previous scene
        gui_screen: GUI screen containing buttons
        overlay: Semi-transparent surface for darkening background
        menu_panel: Solid panel containing the menu
        title_font: Font for "PAUSED" text
        title_text: Rendered "PAUSED" text
    """

    def __init__(self, director):
        """Initialize the ingame menu.

        Args:
            director: Game director instance
        """
        PyGameScene.__init__(self, director)

        # Mark this as an overlay scene so the game below is still visible
        self.is_overlay = True

        # Create the GUI screen
        self.gui_screen = IngameMenuGUIScreen(self)

        # Create overlay surface for semi-transparent background
        self.overlay = pygame.Surface(
            (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)
        )
        self.overlay.set_alpha(OVERLAY_ALPHA)
        self.overlay.fill(OVERLAY_COLOR)

        # Create menu panel surface
        self.menu_panel = pygame.Surface((MENU_WIDTH, MENU_HEIGHT))
        self.menu_panel_rect = self.menu_panel.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT // 2)
        )

        # Initialize font for title
        pygame.font.init()
        self.title_font = pygame.font.SysFont(GUISettings.FONT_TEXT, 36, bold=True)
        self.title_text = self.title_font.render("PAUSED", True, TITLE_COLOR)
        self.title_rect = self.title_text.get_rect(
            centerx=ScreenSettings.SCREEN_WIDTH // 2,
            centery=ScreenSettings.SCREEN_HEIGHT // 2 - 120,
        )

    def update(self, delta_time):
        """Update pause menu state (currently no update logic needed).

        Args:
            delta_time: Milliseconds since last frame
        """
        pass

    def events(self, event_list):
        """Handle input events.

        Args:
            event_list: List of pygame events
        """
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.resumeGame()

        # Pass events to GUI elements (buttons)
        self.gui_screen.events(event_list)

    def render(self, screen):
        """Render the pause menu overlay.

        Renders:
        1. Semi-transparent black overlay
        2. Menu panel background
        3. "PAUSED" title
        4. GUI buttons

        Args:
            screen: pygame.Surface to render on
        """
        # Draw semi-transparent overlay
        screen.blit(self.overlay, (0, 0))

        # Draw menu panel
        self.menu_panel.fill(MENU_BG_COLOR)
        pygame.draw.rect(
            self.menu_panel, MENU_BORDER_COLOR, self.menu_panel.get_rect(), 3
        )
        screen.blit(self.menu_panel, self.menu_panel_rect)

        # Draw title
        screen.blit(self.title_text, self.title_rect)

        # Render GUI elements (buttons)
        self.gui_screen.render(screen)

    def resumeGame(self):
        """Resume the game with a countdown.

        Exits this pause menu and shows a countdown (3-2-1) before
        returning control to the game.
        """
        # Exit this menu first
        self.director.exitScene()
        # Then show countdown before returning to game
        countdown = CountdownScene(self.director)
        self.director.appendScene(countdown)

    def showSettings(self):
        """Open the settings screen."""
        settings_scene = SettingsScene(self.director)
        self.director.appendScene(settings_scene)

    def exitToMainMenu(self):
        """Exit to the main menu.

        Exits both the pause menu and the game scene,
        returning to the main menu.
        """
        # Exit this ingame menu scene
        self.director.exitScene()
        # Exit the game scene (match/gameplay)
        self.director.exitScene()
