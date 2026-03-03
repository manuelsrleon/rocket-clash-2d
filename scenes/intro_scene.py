import pygame
from scene import PyGameScene
from dialogue.dialog_manager import DialogManager
from dialogue.dialog_ui import DialogueUI

class IntroScene(PyGameScene):
    def __init__(self, director):
        super().__init__(director)
        self.screen = getattr(director, "screen", None) or pygame.display.get_surface()
        
        # --- CONFIGURACIÓN DE POSICIÓN ---
        self.fixed_x = 100 
        self.fixed_y = 10   
        self.sprite_size = (604, 326)

        # Carga de datos
        self.manager = DialogManager("dialogues/intro.json")
        self.history = []
        self.max_messages = 2 
        self.font = pygame.font.Font(None, 28)

        # --- CARGA DE ASSETS (Background) ---
        try:
            img = pygame.image.load("assets/backgrounds/background.png").convert()
            self.bg = pygame.transform.scale(img, self.screen.get_size())
        except:
            self.bg = pygame.Surface(self.screen.get_size())
            self.bg.fill((45, 45, 45))

        # --- CARGA DE SPRITES (Tenazas) ---
        self.tenazas_sprites = {}
        chars = self.manager.data.get('characters', {})
        left_data = chars.get('left', {})
        portraits = left_data.get('portraits', {})
        
        if portraits:
            for k, v in portraits.items():
                self.tenazas_sprites[k] = self._load_image(v, self.sprite_size)
        elif left_data.get('portrait'):
            self.tenazas_sprites['idle'] = self._load_image(left_data['portrait'], self.sprite_size)

        self._spawn_current_bubble()

    def _load_image(self, path, size):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except:
            s = pygame.Surface(size, pygame.SRCALPHA)
            s.fill((100, 100, 100, 150)) 
            return s

    def _spawn_current_bubble(self):
        line = self.manager.current_line()
        if not line: return
        
        # 1. Crear instancia temporal para medir altura
        new_bubble = DialogueUI(
            line.get('speaker', 'Tenazas'),
            line.get('text', ''),
            None, # Portrait None porque el sprite grande va arriba
            line.get('side', 'left'),
            self.font
        )

        # 2. Calcular espacio ocupado actual
        start_y = self.fixed_y + self.sprite_size[1] + 10
        current_occupied_y = start_y
        for b in self.history:
            current_occupied_y += b.get_expected_height() + 10
        
        # 3. Lógica de Ciclo
        if current_occupied_y + new_bubble.get_expected_height() > self.screen.get_height() - 20:
            self.history = [] # Limpiar pantalla si no hay espacio

        self.history.append(new_bubble)
        
        # Backup: Limitar por cantidad máxima de mensajes
        if len(self.history) > self.max_messages:
            self.history.pop(0)

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT: 
                self.director.salirPrograma()
                
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.manager.is_line_complete():
                    # Avanzar a la siguiente línea
                    status = self.manager.advance()
                    if status == 'next':
                        self._spawn_current_bubble()
                    else:
                        self.director.exitScene()
                else:
                    # Autocompletar texto animado
                    l = self.manager.current_line()
                    if l:
                        self.manager.char_index = len(l.get('text', ''))

    def update(self, dt):
        dt_seconds = dt / 1000.0
        sm = getattr(self.director, 'settings_manager', None)
        if sm: 
            self.manager.set_speed_multiplier(sm.get_dialogue_speed_multiplier())
        
        # --- ACTUALIZAR ANIMACIÓN DE LAS BURBUJAS ---
        for bubble in self.history:
            bubble.update_anim(dt_seconds)
        
        self.manager.update(dt_seconds)

    def render(self, screen):
        # 1. Fondo
        screen.blit(self.bg, (0, 0))
        
        # 2. Decidir Sprite de Tenazas
        chosen = 'talk' if not self.manager.is_line_complete() else 'idle'
        ten_surf = self.tenazas_sprites.get(chosen)
        if not ten_surf:
            ten_surf = next(iter(self.tenazas_sprites.values()), None)
            
        if ten_surf: 
            screen.blit(ten_surf, (self.fixed_x, self.fixed_y))

        # 3. Dibujar Burbujas acumuladas
        current_y = self.fixed_y + self.sprite_size[1] + 10
        for i, bubble in enumerate(self.history):
            # Determinamos si es la burbuja activa (la última de la lista)
            is_last = (i == len(self.history) - 1)
            
            # Solo animamos el texto (typewriter) si es la última
            if is_last:
                txt = self.manager.get_shown_text()
            else:
                txt = bubble.full_text
                
            y_inc = bubble.draw(screen, current_y, txt, self.fixed_x, is_last=is_last)
            current_y += y_inc