import pygame
import random
from scene import PyGameScene
from dialogue.dialog_manager import DialogManager
from dialogue.dialog_ui import DialogueUI

class DialogueScene(PyGameScene):
    def __init__(self, director, json_path):
        super().__init__(director)
        self.screen = getattr(director, "screen", None) or pygame.display.get_surface()
        
        # --- CONFIGURACIÓN ---
        self.fixed_x = 50
        self.start_y = 50
        self.font = pygame.font.Font(None, 28)
        
        # --- ESTADO DE EFECTOS ---
        self.effects_queue = []
        self.flash_color = None
        self.flash_timer = 0
        self.shake_amount = 0
        self.shake_offset = pygame.Vector2(0, 0)

        # --- DICCIONARIO DE EFECTOS (Mapeo) ---
        self.effect_handlers = {
            "flash": self._handle_flash,
            "shake": self._handle_shake,
            "wait":  self._handle_wait
        }

        # --- GESTIÓN DE DIÁLOGOS ---
        self.manager = DialogManager(json_path)
        self.history = []
        self.max_messages = 4 
        
        bg_path = self.manager.data.get('background', 'assets/backgrounds/background.png')
        try:
            img = pygame.image.load(bg_path).convert()
            self.bg = pygame.transform.scale(img, self.screen.get_size())
        except:
            self.bg = pygame.Surface(self.screen.get_size()); self.bg.fill((30, 30, 30))

        self.portraits = self._load_all_portraits()
        self._spawn_current_bubble()

    # --- FUNCIONES DE DISPARO DE EFECTOS ---
    def _handle_flash(self, data):
        self.flash_color = data.get('color', (255, 255, 255))
        self.flash_timer = 0.15

    def _handle_shake(self, data):
        self.shake_amount = data.get('intensity', 10)

    def _handle_wait(self, data):
        self.flash_color = None 
        self.flash_timer = data.get('seconds', 0.1)

    # --- LÓGICA INTERNA ---
    def _load_all_portraits(self):
        portraits = {}
        chars = self.manager.data.get('characters', {})
        for side in chars:
            char_data = chars[side]
            if char_data.get('portrait'):
                try:
                    img = pygame.image.load(char_data['portrait']).convert_alpha()
                    portraits[char_data['name']] = img
                except: pass
        return portraits

    def _spawn_current_bubble(self):
        line = self.manager.current_line()
        if not line: return
        
        # Añadir eventos a la cola
        self.effects_queue.extend(line.get('events', []))

        new_bubble = DialogueUI(
            line.get('speaker'),
            line.get('text', ''),
            self.portraits.get(line.get('speaker')),
            line.get('side', 'left'),
            self.font
        )

        current_occupied_y = self.start_y
        for b in self.history:
            current_occupied_y += b.get_expected_height() + 10

        if current_occupied_y + new_bubble.get_expected_height() > self.screen.get_height() - 40:
            self.history = []
        
        self.history.append(new_bubble)
        if len(self.history) > self.max_messages: self.history.pop(0)

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT: self.director.salirPrograma()
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.manager.is_line_complete():
                    if self.manager.advance() == 'next':
                        self._spawn_current_bubble()
                    else:
                        self.director.exitScene()
                else:
                    line = self.manager.current_line()
                    if line: self.manager.char_index = len(line.get('text', ''))

    def update(self, dt):
        dt_seconds = dt / 1000.0
        
        for bubble in self.history:
            bubble.update_anim(dt_seconds)
        
        self.manager.update(dt_seconds)

        # 1. Procesar la cola usando el Diccionario
        if self.flash_timer <= 0 and self.effects_queue:
            effect_data = self.effects_queue.pop(0)
            handler = self.effect_handlers.get(effect_data.get('type'))
            if handler:
                handler(effect_data)

        # 2. Actualizar evolución de los efectos activos
        if self.flash_timer > 0:
            self.flash_timer -= dt_seconds
            if self.flash_timer <= 0:
                self.flash_timer = 0
                self.flash_color = None

        if self.shake_amount > 0:
            amt = int(self.shake_amount)
            self.shake_offset.x = random.randint(-amt, amt)
            self.shake_offset.y = random.randint(-amt, amt)
            self.shake_amount -= 60 * dt_seconds 
        else:
            self.shake_amount = 0
            self.shake_offset = pygame.Vector2(0, 0)

    def render(self, screen):
        # 1. Crear superficie temporal para efectos (como el shake)
        temp_surface = pygame.Surface(screen.get_size())
        temp_surface.blit(self.bg, (0, 0))
        
        # 2. Dibujar burbujas sobre temp_surface (¡NO sobre screen!)
        current_y = self.start_y
        for i, bubble in enumerate(self.history):
            is_last = (i == len(self.history) - 1)
            
            txt = self.manager.get_shown_text() if is_last else bubble.full_text
            
            y_inc = bubble.draw(temp_surface, current_y, txt, self.fixed_x, is_last=is_last)
            current_y += y_inc

        # 3. Aplicar la superficie con el offset del Shake a la pantalla real
        screen.blit(temp_surface, (self.shake_offset.x, self.shake_offset.y))

        # 4. Dibujar el Flash encima de todo si existe
        if self.flash_color and self.flash_timer > 0:
            flash_surf = pygame.Surface(screen.get_size())
            flash_surf.fill(self.flash_color)
            flash_surf.set_alpha(150)
            screen.blit(flash_surf, (0, 0))