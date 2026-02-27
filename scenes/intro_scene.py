import pygame
from scene import *
from dialogue.dialog_manager import DialogManager
from dialogue.dialog_ui import DialogueUI

class IntroScene(PyGameScene):
    def __init__(self, director):
        super().__init__(director)
        self.screen = getattr(director, "screen", None) or pygame.display.get_surface()
        if self.screen is None:
            raise RuntimeError("IntroScene necesita una pantalla activa")

        self.manager = DialogManager("dialogues/intro.json")
        self.ui = DialogueUI(self.screen, show_portrait=False)

        # fondo simple
        try:
            img = pygame.image.load("assets/backgrounds/intro_bg.png").convert()
            self.bg = pygame.transform.scale(img, self.screen.get_size())
        except Exception:
            self.bg = pygame.Surface(self.screen.get_size())
            self.bg.fill((150, 150, 150))

        # cargar mapa de sprites para Tenazas (soporta "portraits" dict o "portrait" single)
        chars = self.manager.data.get('characters', {})
        left = chars.get('left', {}) or {}
        portraits = left.get('portraits') or {}
        self.tenazas_sprites = {}
        sprite_size = (704, 376)
        if isinstance(portraits, dict) and portraits:
            for key, path in portraits.items():
                self.tenazas_sprites[key] = self._load_image(path, sprite_size)
        else:
            # fallback a single portrait key
            p = left.get('portrait') or left.get('image')
            if p:
                self.tenazas_sprites['default'] = self._load_image(p, sprite_size)

        # posición centrada sobre la caja de diálogo
        self.tenazas_key_default = 'idle' if 'idle' in self.tenazas_sprites else next(iter(self.tenazas_sprites.keys()), 'default')
        ten = self.tenazas_sprites.get(self.tenazas_key_default)
        if ten:
            self.tenazas_pos = ((self.screen.get_width() - ten.get_width())//2,
                                self.ui.box_rect.y - ten.get_height() - 10)
        else:
            self.tenazas_pos = (self.screen.get_width()//2, self.ui.box_rect.y - 200)

        # aplicar multiplicador de settings si existe
        sm = getattr(director, 'settings_manager', None)
        if sm is not None and hasattr(sm, 'get_dialogue_speed_multiplier'):
            self.manager.set_speed_multiplier(sm.get_dialogue_speed_multiplier())

    def _load_image(self, path, size):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except Exception:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            surf.fill((100,100,100))
            f = pygame.font.Font(None, 24)
            t = f.render("NO IMG", True, (255,255,255))
            surf.blit(t, t.get_rect(center=surf.get_rect().center))
            return surf

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.director.salirPrograma()
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN):
                result = self.manager.advance()
                if result == 'finished':
                    self.director.exitScene()

    def update(self, dt):
        sm = getattr(self.director, 'settings_manager', None)
        if sm is not None and hasattr(sm, 'get_dialogue_speed_multiplier'):
            self.manager.set_speed_multiplier(sm.get_dialogue_speed_multiplier())
        self.manager.update(dt / 1000.0)

    def render(self, screen):
        screen.blit(self.bg, (0, 0))
        line = self.manager.current_line()
        active = line.get('speaker') if line else None

        # decidir sprite: prioridad: line["expression"] -> si no, usar talk/idle/default
        chosen_key = None
        if line:
            expr = line.get('expression')
            if expr and expr in self.tenazas_sprites:
                chosen_key = expr
        if chosen_key is None:
            chosen_key = 'talk' if 'talk' in self.tenazas_sprites else self.tenazas_key_default

        ten_surf = self.tenazas_sprites.get(chosen_key) or next(iter(self.tenazas_sprites.values()), None)
        if ten_surf:
            # pintar Tenazas tal cual (no iluminar/oscurecer)
            screen.blit(ten_surf, self.tenazas_pos)

        # caja de diálogo
        if line:
            name = line.get('speaker') or line.get('name', '')
            text = self.manager.get_shown_text()
            finished = self.manager.is_finished()
            self.ui.draw(name, text, is_complete=finished)
