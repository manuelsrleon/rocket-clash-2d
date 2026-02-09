import pygame
import sys
from scena import *
from pygame.locals import * 

FPS = 60

class Director(): 
    def __init(self):
    def buclePygame(self, escena): 
        reloj = pygame.time.Clock()
        self.salir_escena_pygame = False

        pygame.event.clear()

        while not self.salir_escena_pygame:
            # Pasamos los eventos a la escena
            escena.eventos(pygame.event.get())
            # Actualiza la escena
            escena.update(tiempo_pasado)
            # Se dibuja en pantalla
            escena.dibujar(escena.screen)
            pygame.display.flip()

    def ejecutar(self):
        pygame.init()

        self.screen = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))

        while(len(self.pila)>0):
            escena = self.pila[len(self.pila)-1]
            self.buclePygame(escena)
        else:
            raise Exception("Unrecognized scene type")
        
        pygame.quit()

    def pararEscena(self):
    def salirEscena(self):
    def salirPrograma(self):
    def cambiarEscena(self, escena):
    def apilarEscena(self, escena):
