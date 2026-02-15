import pygame
import os

class DialogueUI:
    def __init__(self, screen, font=None, box_rect=None, portrait_size=(96,96)):
        self.screen = screen
        self.font = font or pygame.font.Font(None, 24)
        self.box_rect = box_rect or pygame.Rect(50, screen.get_height()-170, screen.get_width()-100, 140)
        self.portrait_size = portrait_size
        self.bg_color = (20,20,20)
        self.text_color = (255,255,255)
        self.name_color = (200,200,50)
        self.portrait = None

    def set_portrait(self, path):
        if not path:
            self.portrait = None
            return
        try:
            img = pygame.image.load(path).convert_alpha()
            self.portrait = pygame.transform.smoothscale(img, self.portrait_size)
        except Exception:
            self.portrait = None

    def draw(self, name, text, is_complete=False): 
        pygame.draw.rect(self.screen, self.bg_color, self.box_rect)
        pygame.draw.rect(self.screen, (80,80,80), self.box_rect, 2)

        x = self.box_rect.x + 10
        y = self.box_rect.y + 10

        if self.portrait:
            self.screen.blit(self.portrait, (x, y))
            x += self.portrait_size[0] + 10

        if name:
            name_surf = self.font.render(name, True, self.name_color)
            self.screen.blit(name_surf, (x, y))
            y += name_surf.get_height() + 6

        self._draw_wrapped_text(text, x, y, self.box_rect.w - (x - self.box_rect.x) - 10)

        if is_complete:
            help_surf = self.font.render("Presiona 'Espacio' para continuar...", True, (150, 150, 150))
            help_surf = pygame.transform.scale(help_surf, (int(help_surf.get_width() * 0.8), int(help_surf.get_height() * 0.8)))
            self.screen.blit(help_surf, (self.box_rect.right - help_surf.get_width() - 15, self.box_rect.bottom - help_surf.get_height() - 10))

    def _draw_wrapped_text(self, text, x, y, max_width):
        words = text.split(' ')
        line = ''
        for w in words:
            test = (line + ' ' + w).strip()
            surf = self.font.render(test, True, self.text_color)
            if surf.get_width() <= max_width:
                line = test
            else:
                self.screen.blit(self.font.render(line, True, self.text_color), (x, y))
                y += self.font.get_height() + 2
                line = w
        if line:
            self.screen.blit(self.font.render(line, True, self.text_color), (x, y))