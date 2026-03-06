import pygame
from director import Director
from scenes.dialogue_scene import DialogueScene

def main():
    pygame.init()
    pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Rocket Clash 2D - Dialog Test")

    dir = Director()

    # 2. Crear las escenas en orden: primero intro, luego dialog
    escena_intro = DialogueScene(dir, "dialogues/intro.json")
    escena_dialog_1 = DialogueScene(dir, "dialogues/match1.json")
    escena_dialog_2 = DialogueScene(dir, "dialogues/match2.json")
    escena_dialog_3 = DialogueScene(dir, "dialogues/match3.json")  

    # 3. Apilar las escenas para que el director las gestione
    dir.apilarEscena(escena_dialog_3)
    dir.apilarEscena(escena_dialog_2)
    dir.apilarEscena(escena_dialog_1)
    dir.apilarEscena(escena_intro)
    

    # 4. Lanzar el bucle principal
    dir.ejecutar()

if __name__ == "__main__":
    main()