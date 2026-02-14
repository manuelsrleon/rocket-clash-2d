import pygame
from scene import PyGameScene
from gui_elements import Button, GUIScreen
from settings import ScreenSettings, GUISettings, Colors
from pygame.locals import KEYDOWN, K_ESCAPE
from settings_scene import SettingsScene

# Ingame Menu Constants
OVERLAY_ALPHA = 180
OVERLAY_COLOR = (0, 0, 0)
MENU_WIDTH = 300
MENU_HEIGHT = 350
MENU_BG_COLOR = (50, 50, 70)
MENU_BORDER_COLOR = Colors.WHITE
TITLE_COLOR = Colors.WHITE

class ResumeButton(Button):

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
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        self.screen.menu.resumeGame()


class SettingsButton(Button):

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
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        self.screen.menu.showSettings()


class ExitToMenuButton(Button):

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
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        self.screen.menu.exitToMainMenu()

class IngameMenuGUIScreen(GUIScreen):

    def __init__(self, menu):
        GUIScreen.__init__(self, menu, image=None)

        resume_button = ResumeButton(self)
        settings_button = SettingsButton(self)
        exit_button = ExitToMenuButton(self)

        self.GUIElements.append(resume_button)
        self.GUIElements.append(settings_button)
        self.GUIElements.append(exit_button)

class IngameMenu(PyGameScene):

    def __init__(self, director):
        PyGameScene.__init__(self, director)

        # Mark this as an overlay scene
        self.is_overlay = True

        self.gui_screen = IngameMenuGUIScreen(self)

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

        pygame.font.init()
        self.title_font = pygame.font.SysFont(GUISettings.FONT_TEXT, 36, bold=True)
        self.title_text = self.title_font.render("PAUSED", True, TITLE_COLOR)
        self.title_rect = self.title_text.get_rect(
            centerx=ScreenSettings.SCREEN_WIDTH // 2,
            centery=ScreenSettings.SCREEN_HEIGHT // 2 - 120,
        )

    def update(self, delta_time):
        pass

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.resumeGame()

        # Pass events to GUI elements
        self.gui_screen.events(event_list)

    def render(self, screen):
        screen.blit(self.overlay, (0, 0))

        # Draw menu panel
        self.menu_panel.fill(MENU_BG_COLOR)
        pygame.draw.rect(
            self.menu_panel, MENU_BORDER_COLOR, self.menu_panel.get_rect(), 3
        )
        screen.blit(self.menu_panel, self.menu_panel_rect)
        screen.blit(self.title_text, self.title_rect)
        self.gui_screen.render(screen)

    def resumeGame(self):
        # Exit this menu first
        self.director.exitScene()
        # Then show countdown before returning to game
        from countdown_scene import CountdownScene
        countdown = CountdownScene(self.director)
        self.director.apilarEscena(countdown)

    def showSettings(self):
        settings_scene = SettingsScene(self.director)
        self.director.apilarEscena(settings_scene)

    def exitToMainMenu(self):
        for scene in self.director.scene_stack:
            if len(self.director.scene_stack) == 1:
                break
            self.director.exitScene()
