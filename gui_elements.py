import pygame
from settings import Colors, GUISettings, VolumeController
from assets_manager import SFXAssets
from pygame.locals import *


class GUIElement:
    
    def __init__(self, screen, rectangle):
        self.screen = screen
        self.rect = rectangle
    
    def setPosition(self, position):
        (posX, posY) = position
        self.rect.left = posX
        self.rect.bottom = posY

    def positionInElement(self, position):
        (posX, posY) = position
        return (
            (posX >= self.rect.left)
            and (posX <= self.rect.right)
            and (posY >= self.rect.top)
            and (posY <= self.rect.bottom)
        )

    def render(self):
        raise NotImplemented("Render method not implemented")

    def action(self):
        raise NotImplemented("Action method not implemented")


class Button(GUIElement):
    
    def __init__(
        self,
        screen,
        position=(0, 0),
        size=GUISettings.BUTTON_SIZE,
        text=None,
        font_name=GUISettings.FONT_TEXT,
        font_size=GUISettings.FONT_SIZE,
    ):
        self.screen = screen
        self.hover = False
        self._converted = False
        # non-image button: use a rect, optional text and font
        w, h = size
        rect = pygame.Rect(0, 0, w, h)
        GUIElement.__init__(self, screen, rect)
        self.setPosition(position)
        self.base_rect = self.rect.copy()
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self._font = None
        self.color = Colors.WHITE
        self.border_color = Colors.BLACK
        self.hover_color = Colors.YELLOW

    def render(self, screen):
        color = self.hover_color if self.hover else self.color
        pygame.draw.rect(screen, color, self.base_rect)
        pygame.draw.rect(screen, self.border_color, self.base_rect, 2)

        if self.text:
            if self._font is None:
                try:
                    self._font = pygame.font.SysFont(self.font_name, self.font_size)
                except Exception:
                    pygame.font.init()
                    self._font = pygame.font.SysFont(self.font_name, self.font_size)

            # Render text centered on button
            label_surf = self._font.render(self.text, True, self.border_color)
            label_rect = label_surf.get_rect(center=self.base_rect.center)
            screen.blit(label_surf, label_rect)

    def isHoverInButton(self, position):
        self.hover = self.positionInElement(position)


class GUIScreen:
    
    def __init__(self, menu, image=None):
        self.menu = menu
        self.image = image
        self.GUIElements = []
        self.animations = []

    def events(self, event_list):
        for event in event_list:
            if event.type == MOUSEBUTTONDOWN:
                self.clickElement = None
                for GUIElement in self.GUIElements:
                    if GUIElement.positionInElement(event.pos):
                        self.GUIElementClick = GUIElement

            if event.type == MOUSEBUTTONUP:
                for GUIElement in self.GUIElements:
                    if GUIElement.positionInElement(event.pos):
                        if GUIElement == self.GUIElementClick:
                            try:
                                SFXAssets.load()
                                sound = pygame.mixer.Sound.play(SFXAssets.silbato_corto)
                                sound.set_volume(VolumeController.get_current_volume())
                            except Exception:
                                pass  # Sound not available
                            GUIElement.action()

            if event.type == MOUSEMOTION:
                for GUIElement in self.GUIElements:
                    GUIElement.isHoverInButton(event.pos)

    def render(self, screen):
        if self.image is not None:
            try:
                screen.blit(self.image, self.image.get_rect())
            except Exception:
                pass

        for GUIElement in self.GUIElements:
            GUIElement.render(screen)
