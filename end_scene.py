import pygame
from scene import PyGameScene
from settings import ScreenSettings, GUISettings, Colors
from pygame.locals import *

# Result labels. This is not used. In the future, it will be used for declaring a winner or a tie when the game's over.
RESULT_LABELS = {
    "game_over": "GAME OVER",
    "tie":       "TIE",
    "winner_1":  "PLAYER 1 WINS",
    "winner_2":  "PLAYER 2 WINS",
}

class EndScene(PyGameScene):

    def __init__(self, director, result="game_over"):
        super().__init__(director)

        self.result = result

        self.title_font = pygame.font.SysFont(GUISettings.FONT_TEXT, 96, bold=True)
        self.hint_font  = pygame.font.SysFont(GUISettings.FONT_TEXT, 24)

        label = RESULT_LABELS.get(result, "GAME OVER")
        self.title_surface = self.title_font.render(label, True, Colors.WHITE)
        self.title_rect    = self.title_surface.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT // 2)
        )

        self.hint_surface = self.hint_font.render(
            "Press any key to return to main menu", True, Colors.GRAY_120
        )
        self.hint_rect = self.hint_surface.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT // 2 + 100)
        )

    def update(self, delta_time):
        pass

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                self._exit_to_main_menu()

    def render(self, screen):
        screen.fill(Colors.BLACK)
        screen.blit(self.title_surface, self.title_rect)
        screen.blit(self.hint_surface, self.hint_rect)

    def _exit_to_main_menu(self):
        # Pop all scenes except the first one (main menu), same pattern as IngameMenu
        while len(self.director.scene_stack) > 1:
            self.director.exitScene()
