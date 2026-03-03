import pygame
import random

class DialogueUI:
    def __init__(self, name, full_text, portrait, side, font):
        self.name = name
        self.full_text = full_text
        self.portrait = portrait
        self.side = side 
        self.font = font
        
        # --- SISTEMA DE ANIMACIÓN ---
        self.anim_progress = 0.0 
        self.anim_speed = 8.0   
        self.entry_mode = "pop" # Cambia a "pop" para el efecto de salto

        # Diccionario de funciones de animación
        self.animations = {
            "slide": self._anim_slide,
            "pop":   self._anim_pop
        }
        
        # --- Configuración Visual ---
        self.box_width = 604 
        self.bg_color = (255, 255, 255)
        self.border_color = (0, 0, 0)
        self.text_color = (0, 0, 0)
        self.border_width = 2
        self.portrait_size = (100, 100) 
        self.padding_x = 20
        self.padding_y = 15

    # --- LÓGICA DE LAS ANIMACIONES ---

    def _anim_slide(self, rect, progress):
        """Efecto original: sube desde abajo"""
        offset = 30 * (1.0 - progress)
        rect.y += offset
        return rect

    def _anim_pop(self, rect, progress):
        """Efecto de salto/escalado desde el centro"""
        new_w = rect.width * progress
        new_h = rect.height * progress
        center = rect.center
        new_rect = pygame.Rect(0, 0, new_w, new_h)
        new_rect.center = center
        return new_rect

    def update_anim(self, dt):
        if self.anim_progress < 1.0:
            self.anim_progress += self.anim_speed * dt
            if self.anim_progress > 1.0: self.anim_progress = 1.0

    def draw(self, screen, y_pos, current_text, fixed_x, is_last=False):
        # 1. Calcular Rectángulo Destino
        screen_w = screen.get_width()
        start_x = fixed_x if self.side == 'left' else screen_w - self.box_width - fixed_x
        final_h = self.get_expected_height()
        target_rect = pygame.Rect(start_x, y_pos, self.box_width, final_h)

        # 2. Aplicar Animación desde el Diccionario
        anim_func = self.animations.get(self.entry_mode, self._anim_slide)
        draw_rect = anim_func(target_rect.copy(), self.anim_progress)

        # 3. Dibujar Caja
        if self.anim_progress > 0.05: # Evitar micro-dibujos al inicio
            pygame.draw.rect(screen, self.bg_color, draw_rect, border_radius=5)
            pygame.draw.rect(screen, self.border_color, draw_rect, width=self.border_width, border_radius=5)

            # 4. Dibujar Contenido (solo si la animación está avanzada)
            if self.anim_progress > 0.8:
                self._draw_content(screen, draw_rect, current_text, is_last)

        return final_h + 10

    def _draw_content(self, screen, rect, current_text, is_last=False):
        """Mantiene el dibujo original de retrato y texto e incluye el hint."""
        draw_y = rect.y
        text_margin = 0
        
        if self.portrait:
            p_img = pygame.transform.smoothscale(self.portrait, self.portrait_size)
            portrait_y = draw_y + (rect.height - self.portrait_size[1]) // 2
            text_margin = self.portrait_size[0] + 15
            if self.side == 'right':
                p_x = rect.right - self.portrait_size[0] - self.padding_x
                p_img = pygame.transform.flip(p_img, True, False)
                text_x = rect.x + self.padding_x
            else:
                p_x = rect.x + self.padding_x
                text_x = p_x + text_margin
            screen.blit(p_img, (p_x, portrait_y))
        else:
            text_x = rect.x + self.padding_x

        wrap_width = self.box_width - text_margin - (self.padding_x * 2)
        current_lines = self._wrap_text(current_text, wrap_width)
        line_height = self.font.get_height() + 4
        total_text_h = len(self._wrap_text(self.full_text, wrap_width)) * line_height
        text_block_y = draw_y + (rect.height - total_text_h - 15) // 2
        
        for i, line in enumerate(current_lines):
            t_surf = self.font.render(line, True, self.text_color)
            screen.blit(t_surf, (text_x, text_block_y + i * line_height))

        
        if current_text == self.full_text and is_last:
            small_font = pygame.font.SysFont("sans-serif", 16, bold=True)
            hint_surf = small_font.render("Presiona 'ESPACIO' para continuar", True, (140, 140, 140))
            
            if self.side == 'right':
                hint_x = rect.x + 15
            else:
                hint_x = rect.right - hint_surf.get_width() - 15
                
            hint_y = rect.bottom - hint_surf.get_height() - 10
            screen.blit(hint_surf, (hint_x, hint_y))

    # --- MÉTODOS AUXILIARES ---
    def _wrap_text(self, text, max_w):
        if not text: return []
        words = text.split(' ')
        lines = []; curr = ""
        for w in words:
            if self.font.size((curr + " " + w).strip())[0] <= max_w:
                curr = (curr + " " + w).strip()
            else:
                if curr: lines.append(curr)
                curr = w
        if curr: lines.append(curr)
        return lines

    def get_expected_height(self):
        text_margin = self.portrait_size[0] + 15 if self.portrait else 0
        wrap_width = self.box_width - text_margin - (self.padding_x * 2)
        full_lines = self._wrap_text(self.full_text, wrap_width)
        line_height = self.font.get_height() + 4
        content_h = (len(full_lines) * line_height) + (self.padding_y * 2) + 20 
        min_h = self.portrait_size[1] + (self.padding_y * 2) if self.portrait else 60
        return max(content_h, min_h)