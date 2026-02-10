import pygame
import sys
from scene import *
from pygame.locals import * 

FPS = 60

class Director(): 
    
    def __init__(self):
        self.pila = []
        self.salir_escena_pygame = False
    
    def buclePygame(self, scene): 
        clock = pygame.time.Clock()
        self.salir_escena_pygame = False

        pygame.event.clear()

        while not self.salir_escena_pygame:

            delta_time = clock.tick(FPS)
            scene.events(pygame.event.get())
            # Actualiza la escena
            scene.update(delta_time)
            # Se dibuja en pantalla
            scene.render(scene.screen)
            pygame.display.flip()

    def ejecutar(self):
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        while(len(self.pila)>0):
            escena = self.pila[len(self.pila)-1]
            self.buclePygame(escena)
        else:
            raise Exception("Unrecognized scene type")
        
        pygame.quit()

    def pararEscena(self):
        if(len(self.pila)>0):
            scene = self.pila[len(self.pila)-1]
            if isinstance(scene,PyGameScene):
                self.salir_escena_pygame = True
            else:
                raise Exception("Unrecognized scene type")
    def salirEscena(self):
        self.pararEscena()

        if(len(self.pila)>0):
            self.pila.pop()

    def salirPrograma(self):
        self.pararEscena()
        self.pila = []
    
    def cambiarEscena(self, escena):
        self.pararEscena()
        self.pila.append(escena)
    
    def apilarEscena(self, escena):
        self.pararEscena()
        self.pila.append(escena)