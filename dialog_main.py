import pygame
from director import Director
from scenes.dialogue_scene import DialogueScene

def main():
    # 1. Inicializar el Director
    dir = Director()

    # 2. Crear la escena de diálogo con el JSON de ejemplo
    escena_test = DialogueScene(dir, "dialogues/example.json")

    # 3. Apilar la escena para que el director la gestione
    dir.apilarEscena(escena_test)

    # 4. Lanzar el bucle principal
    dir.ejecutar()

if __name__ == "__main__":
    main()