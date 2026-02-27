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

    # 2. Crear la escena de diálogo con el JSON de ejemplo
    # escena_test = DialogueScene(dir, "dialogues/example.json")
    escena_test = IntroScene(dir) 

    # 3. Apilar la escena para que el director la gestione
    dir.apilarEscena(escena_test)

    # 4. Lanzar el bucle principal
    dir.ejecutar()

if __name__ == "__main__":
    main()