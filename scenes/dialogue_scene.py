import pygame
from scene import *
from dialogue.dialog_manager import DialogManager
from dialogue.dialog_ui import DialogueUI

class DialogueScene(PyGameScene):
    def __init__(self, director, json_path):
        super().__init__(director)
        self.manager = DialogManager(json_path)

        # Asegurar que tenemos una Surface válida: preferir self (establecido por PyGameScene),
        # luego director.screen, y finalmente pygame.display.get_surface() como fallback.
        self.screen = getattr(self, "screen", None) or getattr(director, "screen", None) or pygame.display.get_surface()
        if self.screen is None:
            raise RuntimeError("No screen available for DialogueScene; initialize display first and set director.screen")

        self.ui = DialogueUI(self.screen)
        
        # Cargar el primer retrato si existe
        self._update_portrait()

    def _update_portrait(self):
        line = self.manager.current_line()
        if line and 'portrait' in line:
            self.ui.set_portrait(line['portrait'])

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.director.salirPrograma()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    result = self.manager.advance()
                    if result == 'finished':
                        # Cerramos la escena de diálogo y volvemos a la anterior en la pila
                        self.director.exitScene()
                    elif result == 'next':
                        # Si pasamos a una nueva línea, actualizamos el retrato
                        self._update_portrait()

    def update(self, dt):
        self.manager.update(dt / 1000.0) 

    def render(self, screen):
        screen.fill((0, 0, 0)) 
        line = self.manager.current_line()
        if line:
            name = line.get('name', '')
            text = self.manager.get_shown_text()
            
            # Comprobamos si el manager ya terminó de escribir la frase actual
            finished = self.manager.is_finished() 
            
            # Pasamos ese dato a la UI
            self.ui.draw(name, text, is_complete=finished)