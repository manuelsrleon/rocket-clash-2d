import pygame
from scene import *
from pygame.locals import*

class GUIElement:
    def __init__(self,screen,rectangle):
        self.screen = screen
        self.rect = rectangle
    
    def setPosition(self,position):
        (posX, posY) = position
        self.rect.left = posX
        self.rect.bottom = posY

    def positionInElement(self, position):
        (posX, posY) = position
        return (posX >= self.rect.left) and (posX <= self.rect.right) and (posY >= self.rect.top) and (posY <= self.rect.bottom)

    def render(self):
        raise NotImplemented("Render method not implemented")
    def action(self):
        raise NotImplemented("Action method not implemented")

class Button(GUIElement):
    
    def __init__(self, screen, imageName, position):
        self.image =  pygame.image.load("assets/gui/play_button.png").convert_alpha()# add img loading logic
        #self.image = pygame.transform.scale(self.image, self.)
        GUIElement.__init__(self, screen, self.image.get_rect())
        self.setPosition(position)
    
    def render(self, screen):
        screen.blit(self.image, self.rect)

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

class GUIScreen:
    def __init__(self,menu,imageName):
        self.menu = menu
        self.image = pygame.image.load("assets/gui/"+imageName)
        self.image = pygame.transform.scale(self.image, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.GUIElements = []
        self.animations = []

    def events(self, event_list):
        for event in event_list:
            if event.type == MOUSEBUTTONDOWN:
                self.clickElement = None
                for GUIElement in self.GUIElements:
                    if GUIElement.positionInElement(event.position):
                        self.GUIElementClick = GUIElement
                        
            if event.type == MOUSEBUTTONUP:
                for GUIElement in self.GUIElements:
                    if GUIElement.positionInElement(event.pos):
                        if(GUIElement == self.GUIElementClick):
                            GUIElement.action()
    
    def render(self, screen):
        screen.blit(self.image, self.image.get_rect())
        for GUIElement in self.GUIElements:
            GUIElement.render(screen)

class InitialGUIScreen(GUIScreen):
    def __init__(self, menu, imageName):
        GUIScreen.__init__(self, menu, imageName)
        playButton = PlayButton(self)
        exitButton = ExitButton(self)
        self.GUIElements.append(playButton)
        self.GUIElements.append(exitButton)

class Menu(PyGameScene):
    def __init__(self, director):
        PyGameScene.__init__(self,director)
        self.screenList = []
        self.screenList.append(InitialGUIScreen(self, "main_menu_bg.png"))
        self.showInitialScreen()
    def update(self, *args):
        return
    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.exit()
            elif event.type == pygame.QUIT:
                self.director.exitScene()
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