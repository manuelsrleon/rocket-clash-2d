import pygame, sys, os
from pygame.locals import *

class MySprite(pygame.sprite.Sprite):

    #body_img = None
    #wheel_img = None

    #body_img = pygame.image.load('./assets/cars/'+carType+'_car.png').convert_alpha()
    #wheel_img = pygame.image.load('./assets/cars/wheels/wheel.y png').convert_alpha()

    def __init__(self, carPos, carType):
        self.position = (0,0) #m * m 
        self.velocity = (0,0) #m/s X, m/s Y
        self.acceleration = (0,0) #m/s² X m/s Y

    #This should be rewritten to be physics based
    def computePosition(self,deltaPos):
        (posX, posY) = self.position
        (deltaX, deltaY) = deltaPos
        self.setPosition((posX+deltaX, posY+deltaY))
    def update(self, deltaTime):
        deltaX = self.velocity[0]*deltaTime
        deltaY = self.velocity[1]*deltaTime
        self.computePosition((deltaX,deltaY))

    
    def render(display): 
        self.blit(wheel_img, (30,0))
        self.blit(wheel_img, (70,0))

class Car(MySprite):
    def __init__():
        Exception("NotImplemented")
    #def move(self, move)
    #def update()
    #
#class PlayerCar(Car):
    #def __init__(self):
    #def move():
