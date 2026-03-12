import pygame
import sys
import os
from scene import PyGameScene
from settings import ScreenSettings, Colors, GUISettings
from assets_manager import Assets, BACKGROUNDS_PATH
from pygame.locals import *

class CreditsScene(PyGameScene):
    def __init__(self, director):
        super().__init__(director)
        
        # 1. Registro dinámico de fondo (por si no está en Assets)
        if "credits_bg" not in Assets._IMAGE_DATA:
            Assets._IMAGE_DATA["credits_bg"] = (
                "credits_background.png", 
                BACKGROUNDS_PATH, 
                (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)
            )

        self.background = Assets.get_image("credits_bg")

        # Configuración de scroll
        self.scroll_speed = 0.9
        self.y_offset = ScreenSettings.SCREEN_HEIGHT
        
        # Fuentes
        self.font_role = pygame.font.SysFont(GUISettings.FONT_TEXT, 40, italic=True)
        self.font_name = pygame.font.SysFont(GUISettings.FONT_TEXT, 30)

        # Contenido de créditos
        # Añadimos un par de "" al final para dar aire antes del cierre
        self.credits_list = [
            ("DIRECTION", ["Samuel Acebo Rega", "Levi Barros García", "Brais Piñeiro Lozano", "Andrés Romano Seijas", "Manuel Santamariña Ruiz de León"]),
            ("PRODUCED BY", ["ACabra Riazor Film Studios"]),
            ("IMPLEMENTED WITH", ["Pygame & Python"]),
            ("VISUAL ART", ["Gemini y Nano Banana", "(Los mejores artistas del mundo)"]),
            ("MUSIC", ["OpenGameArt & Freesound"]),
            ("SPECIAL THANKS", ["The Open Source Community", "Stack Overflow Contributors"]),
            ("LEGAL & COPYRIGHT", ["© 2024-2026 ACabra Riazor Film Studios", "All rights reserved"]),
            ("", ["THANKS FOR PLAYING :)"]),
            ("", [""]), 
            ("", [""])
        ]

        self.rendered_texts = self._prepare_credits()
        self.total_height = len(self.rendered_texts) * 45 

        # Estado de salida
        self.is_exiting = False
        self.wait_timer = 0  
        
        self.fade_from_black()

    def _prepare_credits(self):
        surfaces = []
        for role, names in self.credits_list:
            if role:
                surfaces.append(self.font_role.render(role, True, Colors.YELLOW))
            for name in names:
                surfaces.append(self.font_name.render(name, True, Colors.WHITE))
            surfaces.append(None) # Espaciador
        return surfaces

    def events(self, event_list):
        # Hemos quitado la detección de teclas para evitar el salto de créditos
        for ev in event_list:
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def _start_exit_transition(self):
        """Inicia la salida automática al finalizar el scroll."""
        if self.is_exiting: return
        self.is_exiting = True
        
        # Bajamos la música suavemente para un final elegante
        pygame.mixer.music.fadeout(2000)
        
        # Fundido a negro
        self.fade_to_black(callback=self._set_wait_timer)

    def _set_wait_timer(self):
        """Activa el tiempo de espera en negro antes de cerrar el proceso."""
        self.wait_timer = 2.0 

    def _exit_game_completely(self):
        """Vuelve al menú principal en vez de cerrar el juego."""
        if hasattr(self.director, 'in_campaign') and self.director.in_campaign:
            self.director.advance_campaign()
        else:
            # Pop back to main menu
            self.director.exitScene()

    def update(self, dt):
        dt_sec = dt / 1000.0
        self.update_fade(dt)
        
        # Lógica de espera post-créditos
        if self.is_exiting and self.wait_timer > 0:
            self.wait_timer -= dt_sec
            if self.wait_timer <= 0:
                self._exit_game_completely()
            return

        # Solo mover el scroll si no hemos iniciado la salida
        if not self.is_exiting:
            self.y_offset -= self.scroll_speed
            
            # Al terminar los textos, se activa la transición automáticamente
            if self.y_offset < -self.total_height:
                self._start_exit_transition()

    def render(self, screen):
        # Dibujo de fondo
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(Colors.BLACK)

        # Capa de oscurecimiento para legibilidad
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(120); overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Dibujo de los textos renderizados
        curr_y = self.y_offset
        center_x = ScreenSettings.SCREEN_WIDTH // 2
        
        for surf in self.rendered_texts:
            if surf:
                rect = surf.get_rect(center=(center_x, int(curr_y)))
                # Culling básico: solo dibujamos lo que está en pantalla
                if -50 < curr_y < ScreenSettings.SCREEN_HEIGHT + 50:
                    screen.blit(surf, rect)
            curr_y += 45

        # Capa de fundido (Fade)
        self.draw_fade(screen)