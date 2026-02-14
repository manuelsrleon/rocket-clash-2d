import pygame
from match_scene import MatchScene
from scene import PyGameScene
from gui_elements import Button, GUIScreen
from assets_manager import GUIAssets
from settings import ScreenSettings
from settings_scene import SettingsScene
from pygame.locals import KEYDOWN, K_ESCAPE, QUIT

class PlayButton(Button):

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
        self.screen.menu.playCampaign()


class SettingsButton(Button):

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
        self.screen.menu.showSettingsScreen()


class ExitButton(Button):

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
        self.screen.menu.exit()

class InitialGUIScreen(GUIScreen):

    def __init__(self, menu):
        try:
            GUIAssets.load()
            bg_image = GUIAssets.main_menu_bg
        except Exception:
            bg_image = None
        
        GUIScreen.__init__(self, menu, bg_image)

        playButton = PlayButton(self)
        exitButton = ExitButton(self)
        settingsButton = SettingsButton(self)

        self.GUIElements.append(playButton)
        self.GUIElements.append(exitButton)
        self.GUIElements.append(settingsButton)

class Menu(PyGameScene):

    def __init__(self, director):
        PyGameScene.__init__(self, director)
        self.screenList = []

        self.screenList.append(InitialGUIScreen(self))
        self.showInitialScreen()

    def update(self, *args):
        return

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.exit()
            elif event.type == QUIT:
                self.director.exitScene()
        # Pass events to the current GUI screen
        self.screenList[self.currentScreen].events(event_list)

    def render(self, screen):
        self.screenList[self.currentScreen].render(screen)

    def exit(self):
        self.director.exitScene()

    def playCampaign(self):
        campaignScene = MatchScene(self.director)
        self.director.apilarEscena(campaignScene)
        self.currentScreen = len(self.screenList) - 1

    def showInitialScreen(self):
        self.currentScreen = 0

    def showSettingsScreen(self):
        settingsScreen = SettingsScene(self.director)
        self.director.apilarEscena(settingsScreen)
        self.currentScreen = len(self.screenList) - 1
