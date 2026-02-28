import pygame
from director import Director
from scenes.dialogue_scene import DialogueScene
from scenes.intro_scene import IntroScene

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Rocket Clash 2D - Dialog Test")

    dir = Director()
    dir.screen = screen

    # 2. Crear las escenas en orden: primero intro, luego dialog
    escena_intro = IntroScene(dir)
    escena_dialog = DialogueScene(dir, "dialogues/example.json")

    # 3. Apilar las escenas para que el director las gestione
    dir.apilarEscena(escena_dialog)
    dir.apilarEscena(escena_intro)
    

    # 4. Lanzar el bucle principal
    dir.ejecutar()

if __name__ == "__main__":
    main()