import pygame
from scene import *
from dialogue.dialog_manager import DialogManager
from dialogue.dialog_ui import DialogueUI

class DialogueScene(PyGameScene):
    def __init__(self, director, json_path):
        super().__init__(director)
        self.manager = DialogManager(json_path)

        # asegurar pantalla válida
        self.screen = getattr(self, "screen", None) or \
                      getattr(director, "screen", None) or \
                      pygame.display.get_surface()
        if self.screen is None:
            raise RuntimeError("No screen available for DialogueScene; initialize display first and set director.screen")

        # UI sin retrato interior
        self.ui = DialogueUI(self.screen, show_portrait=False)

        # dimensiones de los retratos laterales
        self.char_size = (180, 180)
        self.left_name = None
        self.right_name = None
        self.left_surf = None
        self.right_surf = None
        self._setup_characters()

        # fondo de prueba (puedes cargar un PNG en lugar de esto)
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg.fill((30, 50, 90))
        font = pygame.font.Font(None, 72)
        txt = font.render("Fondo1", True, (200,200,200))
        self.bg.blit(txt, txt.get_rect(center=self.bg.get_rect().center))

        # no hay retrato dentro de la caja
        self._update_portrait()

    def _setup_characters(self):
        chars = self.manager.data.get('characters', {})

        def load(path):
            try:
                img = pygame.image.load(path).convert_alpha()
            except Exception:
                img = pygame.Surface(self.char_size, pygame.SRCALPHA)
                img.fill((100,100,100))
                f = pygame.font.Font(None, 24)
                t = f.render("NO IMG", True, (255,255,255))
                img.blit(t, t.get_rect(center=img.get_rect().center))
            return pygame.transform.smoothscale(img, self.char_size)

        if 'left' in chars:
            self.left_name = chars['left'].get('name')
            self.left_surf = load(chars['left'].get('portrait'))
        if 'right' in chars:
            self.right_name = chars['right'].get('name')
            self.right_surf = load(chars['right'].get('portrait'))

        # compatibilidad con el formato antiguo
        if self.left_surf is None or self.right_surf is None:
            seen = []
            for l in self.manager.lines:
                n = l.get('speaker') or l.get('name')
                if n and n not in seen:
                    seen.append(n)
            if seen and self.left_surf is None:
                self.left_name = seen[0]
                line = next(l for l in self.manager.lines
                            if (l.get('speaker') or l.get('name')) == seen[0])
                self.left_surf = load(line.get('portrait'))
            if len(seen) >= 2 and self.right_surf is None:
                self.right_name = seen[1]
                line = next(l for l in self.manager.lines
                            if (l.get('speaker') or l.get('name')) == seen[1])
                self.right_surf = load(line.get('portrait'))

    def _update_portrait(self):
        self.ui.set_portrait(None)

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.director.salirPrograma()
            if event.type == pygame.KEYDOWN and \
               (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN):
                result = self.manager.advance()
                if result == 'finished':
                    self.director.exitScene()
                elif result == 'next':
                    self._update_portrait()

    def update(self, dt):
        # refrescar multiplicador de velocidad (SettingsManager)
        sm = getattr(self.director, 'settings_manager', None) or \
             getattr(self.director, 'settings', None) or \
             getattr(self.director, 'settingsManager', None)
        if sm is not None and hasattr(sm, 'get_dialogue_speed_multiplier'):
            self.manager.set_speed_multiplier(sm.get_dialogue_speed_multiplier())

        self.manager.update(dt / 1000.0)

    def render(self, screen):
        screen.blit(self.bg, (0,0))

        line = self.manager.current_line()
        active = None
        if line:
            active = line.get('speaker') or line.get('name')
        self._draw_characters(screen, active)

        if line:
            name = line.get('speaker') or line.get('name', '')
            text = self.manager.get_shown_text()
            finished = self.manager.is_finished()
            self.ui.draw(name, text, is_complete=finished)

    def _draw_characters(self, screen, active_name):
        def rend(surf, name, x):
            if surf is None:
                return
            is_active = (name is not None and name == active_name)

            # primero escalamos el sprite
            w, h = surf.get_size()
            scale = 1.2 if is_active else 1.0
            tmp = pygame.transform.smoothscale(surf,
                                               (int(w * scale), int(h * scale)))

            if is_active:
                # aclarar un poco: sumar ~60 a cada canal RGB, no al alfa
                hl = tmp.copy()
                hl.fill((60, 60, 60, 0),
                        special_flags=pygame.BLEND_RGB_ADD)
                tmp.blit(hl, (0, 0))
            else:
                # oscurecer sin llegar a negro absoluto
                sh = tmp.copy()
                sh.fill((120, 120, 120, 0),
                        special_flags=pygame.BLEND_RGB_MULT)
                tmp.blit(sh, (0, 0))

            pos = (x, self.ui.box_rect.y - tmp.get_height() - 10)
            screen.blit(tmp, pos)

        if self.left_surf:
            rend(self.left_surf, self.left_name, self.ui.box_rect.x)
        if self.right_surf:
            x = self.ui.box_rect.right - self.char_size[0]
            rend(self.right_surf, self.right_name, x)