import pygame, sys
from pygame.locals import *

pygame.init()

WHITE = (255,255,255)

screen = pygame.display.set_mode((800,600))

screen.fill((0,0,0))

pygame.draw.circle(screen, WHITE, (50,50),4,0)

pygame.display.update()

pygame.quit()

sys.exit()