import pygame, sys, os
from pygame.locals import *

# CONSTANTES FÍSICAS (Basadas en la teoría)
GRAVEDAD = 0.0003  # Píxeles / ms² 
MOVIMIENTOS = {'QUIETO': 0, 'IZQUIERDA': 1, 'DERECHA': 2, 'ARRIBA': 3}
POSTURAS = {'QUIETO': 0, 'ANDANDO': 1, 'SALTANDO': 2}

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
    def __init__(self, carType, pos_inicial):
        super().__init__()
        # Carga de imagen de coche (No sé si está aún)
        ruta_img = os.path.join('assets', 'cars', f'{carType}_car.png')
        self.image = pygame.image.load(ruta_img).convert_alpha()
        self.rect = self.image.get_rect()
        
        self.establecerPosicion(pos_inicial)
        
        # Configuración de movimiento
        self.velocidadCarrera = 0.3 
        self.velocidadSalto = 0.4
        self.numPostura = POSTURAS['QUIETO']

    def mover(self, teclas, arriba, izquierda, derecha):
        vx, vy = self.velocidad

        # Movimiento Horizontal
        if teclas[izquierda]:
            vx = -self.velocidadCarrera
        elif teclas[derecha]:
            vx = self.velocidadCarrera
        else:
            vx = 0

        # Lógica de Salto (Solo si está en el suelo)
        if teclas[arriba] and self.numPostura != POSTURAS['SALTANDO']:
            vy = -self.velocidadSalto
            self.numPostura = POSTURAS['SALTANDO']

        self.velocidad = [vx, vy]

    def update(self, tiempo):
        vx, vy = self.velocidad

        # Aplicar gravedad si está saltando 
        if self.numPostura == POSTURAS['SALTANDO']:
            vy += GRAVEDAD * tiempo
            self.velocidad[1] = vy

        super().update(tiempo)

        # Simulación de suelo (Ajustar según altura de estadio el 550)
        if self.posicion[1] >= 550:
            self.establecerPosicion((self.posicion[0], 550))
            self.velocidad[1] = 0
            self.numPostura = POSTURAS['QUIETO']

# Funcionalidad pelota
class Ball(MySprite):
    def __init__(self, pos_inicial):
        super().__init__()
        ruta_img = os.path.join('assets', 'ball', 'ball.png')
        self.image = pygame.image.load(ruta_img).convert_alpha()
        self.rect = self.image.get_rect()
        
        self.establecerPosicion(pos_inicial)
        self.velocidad = [0, 0]

    def update(self, tiempo):
        vx, vy = self.velocidad
        
        # Física de la pelota: Gravedad y Rozamiento
        vy += 0.0002 * tiempo #Nos interesa que caiga un pelin mas lento
        vx *= 0.98 # Rozamiento para que se detenga
        
        self.velocidad = [vx, vy]
        super().update(tiempo)

        # Rebote en suelo
        if self.posicion[1] >= 550:
            self.establecerPosicion((self.posicion[0], 550))
            self.velocidad[1] *= -0.6 # Pierde fuerza al botar