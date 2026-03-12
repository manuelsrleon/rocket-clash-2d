import pygame
from match_scene import MatchScene
from scene import PyGameScene
from gui_elements import Button, GUIScreen
from assets_manager import Assets
from settings import ScreenSettings
from settings_scene import SettingsScene, GUISettings
from first_scene import FirstScene
from third_scene import ThirdScene
from second_scene import SecondScene
from pygame.locals import KEYDOWN, K_ESCAPE, QUIT

class PlayButton(Button):

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(
                ScreenSettings.SCREEN_WIDTH // 2 - GUISettings.BUTTON_SIZE[0] // 2,
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
                ScreenSettings.SCREEN_WIDTH // 2 - GUISettings.BUTTON_SIZE[0] // 2,
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
                ScreenSettings.SCREEN_WIDTH // 2 - GUISettings.BUTTON_SIZE[0] // 2,
                ScreenSettings.SCREEN_HEIGHT - 78,
            ),
            text="Exit",
        )

    def action(self):
        self.screen.menu.exit()

class InitialGUIScreen(GUIScreen):

    def __init__(self, menu):
        try:
            bg_image = Assets.get_image("main_menu_bg")
        except Exception:
            bg_image = None
        
        GUIScreen.__init__(self, menu, bg_image)

        playButton = PlayButton(self)
        settingsButton = SettingsButton(self)
        exitButton = ExitButton(self)

        self.GUIElements.append(playButton)
        self.GUIElements.append(settingsButton)
        self.GUIElements.append(exitButton)

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
        from scenes.dialogue_scene import DialogueScene
        from scenes.credits_scene import CreditsScene

        d = self.director
        sequence = [
            # lambda: DialogueScene(d, "dialogues/intro.json"),
            # lambda: DialogueScene(d, "dialogues/match1.json"),
            lambda: FirstScene(d),
            lambda: DialogueScene(d, "dialogues/match1_end.json"),
            lambda: DialogueScene(d, "dialogues/match2.json"),
            lambda: SecondScene(d),
            lambda: DialogueScene(d, "dialogues/match2_end.json"),
            lambda: DialogueScene(d, "dialogues/match3.json"),
            lambda: ThirdScene(d),
            lambda: DialogueScene(d, "dialogues/match3_end.json"),
            lambda: CreditsScene(d),
        ]
        d.start_campaign(sequence)

    def showInitialScreen(self):
        self.currentScreen = 0

    def showSettingsScreen(self):
        settingsScreen = SettingsScene(self.director)
        self.director.apilarEscena(settingsScreen)
        self.currentScreen = len(self.screenList) - 1
