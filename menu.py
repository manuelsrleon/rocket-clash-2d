import pygame
from scene import *

class GUIElement:
    def __init__(self,pantalla,rectangle):
        self.screen = screen
        self.rect = rectangle
    
    def setPosition(self,position):
        (posX, posY) = position
        self.rect.left = posX
        self.rect.bottom = posY

    def render(self):
        raise NotImplemented("Render method not implemented")
    def action(self):
        raise NotImplemented("Action method not implemented")

class Button(GUIElement):
    def __init__(self, screen, imageName, position):
        self.image = None # add img loading logic
        self.image = pygame.transform.scale(self.image, (20,20))
        GUIElement.__init__(self, screen, self.image.get_rect())
        self.setPosition(position)

class PlayButton(Button):
    def __init__(self,screen):
        Button.__init__(self, screen, 'play_button.png', (580, 530))
    def action(self):
        self.screen.menu.playCampaign()

class ExitButton(Button):
    def __init__(self, screen):
        Button.__init__(self, screen, 'exit_button.png', (580, 560))
    def action(self):
        self.screen.menu.exit()

class Menu(PyGameScene):
    def __init(self, director):
        PyGameScene.__init__(self,director)
        self.screenList = []
        self.screenList.append(InitialGUISscreen(self))
        self.showInitialScreen
    def update(self, *args):
        return
    def events(self, event_list):
        for event in event_list:
            if event_type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.exit()
            elif event.type == pygame.QUIT:
                self.director.exit()
        self.screenList[self.currentScreen].events(event_list)

    def render(self,screen):
        self.screenList[self.currentScreen].render(screen)
    
    def exit(self):
        self.director.exit()
    
    def playCampaign(self):
        scene = MatchScene(self.director)
        self.director.appendScene(scene)
    
    def showInitialScreen(self):
        self.currentScreen = 0