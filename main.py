
import pygame

from match_scene import MatchScene
from director import Director
from menu import Menu

screen = None

if __name__ == '__main__':
    director = Director()
    escena = Menu(director)
    director.apilarEscena(escena)
    director.ejecutar()