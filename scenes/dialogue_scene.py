import pygame
import random
from scene import PyGameScene
from dialogue.dialog_manager import DialogManager
from dialogue.dialog_ui import DialogueUI
from dialogue.dialogue_sound_player import DialogueSoundPlayer

class DialogueScene(PyGameScene):
    def __init__(self, director, json_path):
        super().__init__(director)
        self.screen = getattr(director, "screen", None) or pygame.display.get_surface()
        sw, sh = self.screen.get_size()

        # --- CONFIGURACIÓN DE POSICIONES FIJAS (Top-Down) ---
        self.font = pygame.font.Font(None, 28)
        self.base_sprite_size = (600, 325)
        
        self.fixed_sprite_y = 40        # Margen superior
        self.margin_side = 10           # Pegados a los lados
        self.sprite_to_bubble_gap = 10  # Espacio entre el coche y la primera caja
        self.bubble_gap = 8             # Espacio entre cajas y margen inferior

        # --- GESTIÓN DE DIÁLOGOS ---
        self.manager = DialogManager(json_path)
        self.history = []
        
        num_chars = len(self.manager.data.get('characters', {}))
        self.scale_factor = 0.75 if num_chars > 1 else 1.0
        self.current_w = int(self.base_sprite_size[0] * self.scale_factor)
        self.current_h = int(self.base_sprite_size[1] * self.scale_factor)

        # Coordenada Y donde empezará SIEMPRE la primera burbuja
        self.start_bubbles_y = self.fixed_sprite_y + self.current_h + self.sprite_to_bubble_gap

        # --- CARGA DE ASSETS ---
        self.bg = self._load_bg(self.manager.data.get('background', 'assets/backgrounds/background.png'))
        self.character_sprites = self._load_characters()
        
        # --- SISTEMA DE SONIDO DE VOCES ---
        sound_config = {
            "Tenazas": ["assets/sfx/dialog_1.ogg"],
            "Ruedaldinho": [f"assets/sfx/dialog_text_{i}.ogg" for i in range(1, 5)],
            "default": ["assets/sfx/dialog_2.ogg"]
        }
        self.audio_player = DialogueSoundPlayer(sound_config)
        self.audio_player.set_interval_by_speed(self.manager.base_speed)
        
        # --- MÚSICA: CONTROL AUTÓNOMO ---
        self.bgm_path = self.manager.data.get('music')
        self.music_started = False  # Flag para evitar que suene antes de tiempo

        # --- ESTADO DE EFECTOS ---
        self.effects_queue = []
        self.flash_timer = 0
        self.flash_color = None
        self.shake_offset = pygame.Vector2(0, 0)
        self.shake_amount = 0
        
        self.effect_handlers = {
            "flash": self._handle_flash, 
            "shake": self._handle_shake, 
            "wait": self._handle_wait
        }

        self._spawn_current_bubble()

    def _load_bg(self, path):
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, self.screen.get_size())
        except:
            s = pygame.Surface(self.screen.get_size()); s.fill((30, 30, 30)); return s

    def _load_characters(self):
        sprites = {}
        chars_data = self.manager.data.get('characters', {})
        for side_key, data in chars_data.items():
            name = data.get('name')
            if not name: continue
            sprites[name] = {"side": side_key}
            portraits = data.get('portraits', {"idle": data.get('portrait')})
            for state, path in portraits.items():
                if path:
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        img = pygame.transform.smoothscale(img, (self.current_w, self.current_h))
                        sprites[name][state] = img
                    except: pass
            if "idle" in sprites[name] and "talk" not in sprites[name]:
                sprites[name]["talk"] = sprites[name]["idle"]
        return sprites

    def _spawn_current_bubble(self):
        line = self.manager.current_line()
        if not line: return
        self.effects_queue.extend(self.manager.get_current_events())
        self.audio_player.reset()
        
        new_speaker = line.get('speaker')
        new_side = line.get('side', 'left')
        
        if self.history:
            last_bubble = self.history[-1]
            last_speaker = getattr(last_bubble, 'name', None) or getattr(last_bubble, 'speaker', None)
            if new_speaker != last_speaker:
                self.history = []

        new_bubble = DialogueUI(new_speaker, line.get('text', ''), None, new_side, self.font)
        current_y_cursor = self.start_bubbles_y
        for b in self.history:
            current_y_cursor += b.get_expected_height() + self.bubble_gap
        
        if current_y_cursor + new_bubble.get_expected_height() > (self.screen.get_height() - self.bubble_gap):
            self.history = []

        self.history.append(new_bubble)

    def update(self, dt):
        # --- DISPARO DE MÚSICA AL COMENZAR LA ESCENA ---
        if not self.music_started:
            if self.bgm_path:
                self._start_music(self.bgm_path)
            else:
                # Si entramos en una escena sin música, silenciamos la anterior
                self._stop_music()
            self.music_started = True

        dt_sec = dt / 1000.0
        old_idx = int(self.manager.char_index)
        
        sm = getattr(self.director, 'settings_manager', None)
        if sm: 
            self.manager.set_speed_multiplier(sm.get_dialogue_speed_multiplier())
        
        self.manager.update(dt_sec)
        new_idx = int(self.manager.char_index)
        
        if new_idx > old_idx:
            line = self.manager.current_line()
            if line:
                text = line.get('text', '')
                speaker_name = line.get('speaker', 'default')
                for i in range(old_idx, new_idx):
                    if i < len(text):
                        self.audio_player.play_check(text[i], speaker_name)

        for b in self.history: 
            b.update_anim(dt_sec)
        
        if self.flash_timer <= 0 and self.effects_queue:
            eff = self.effects_queue.pop(0)
            handler = self.effect_handlers.get(eff.get('type'))
            if handler: handler(eff)
            
        if self.flash_timer > 0:
            self.flash_timer -= dt_sec
            if self.flash_timer <= 0: self.flash_color = None
            
        if self.shake_amount > 0:
            amt = int(self.shake_amount)
            self.shake_offset.x = random.randint(-amt, amt)
            self.shake_offset.y = random.randint(-amt, amt)
            self.shake_amount -= 60 * dt_sec
        else: 
            self.shake_offset = pygame.Vector2(0, 0)

    def render(self, screen):
        sw, sh = screen.get_size()
        temp_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        temp_surf.blit(self.bg, (0, 0))

        current_line = self.manager.current_line()
        speaker_now = current_line.get('speaker') if current_line else None
        num_chars_in_scene = len(self.character_sprites)

        pos_map = {
            "left":   (self.margin_side, self.fixed_sprite_y),
            "middle": ((sw // 2) - (self.current_w // 2), self.fixed_sprite_y),
            "right":  (sw - self.current_w - self.margin_side, self.fixed_sprite_y)
        }

        for char_name, char_info in self.character_sprites.items():
            is_speaking = (char_name == speaker_now)
            side = char_info.get("side", "middle")
            pos_key = "middle" if num_chars_in_scene <= 1 else side
            draw_pos = pos_map.get(pos_key, pos_map["middle"])
            
            state = "talk" if (is_speaking and not self.manager.is_line_complete()) else "idle"
            img = char_info.get(state) or char_info.get("idle")
            
            if img:
                if num_chars_in_scene > 1 and not is_speaking:
                    shaded = img.copy()
                    shaded.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    temp_surf.blit(shaded, draw_pos)
                else:
                    temp_surf.blit(img, draw_pos)

        current_y = self.start_bubbles_y
        for i, bubble in enumerate(self.history):
            is_last = (i == len(self.history) - 1)
            txt = self.manager.get_shown_text() if is_last else bubble.full_text
            draw_x = (sw // 2) - (self.current_w // 2) if num_chars_in_scene <= 1 else 50
            y_inc = bubble.draw(temp_surf, current_y, txt, draw_x, is_last=is_last)
            current_y += y_inc + self.bubble_gap

        screen.blit(temp_surf, (self.shake_offset.x, self.shake_offset.y))
        if self.flash_color and self.flash_timer > 0:
            f = pygame.Surface(screen.get_size()); f.fill(self.flash_color)
            f.set_alpha(150); screen.blit(f, (0, 0))

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT: 
                self.director.salirPrograma()
            
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.manager.is_line_complete():
                    result = self.manager.advance()
                    if result == 'next': 
                        self._spawn_current_bubble()
                    elif result == 'finished': 
                        # Detenemos música justo antes de salir de la escena
                        self._stop_music()
                        self.director.exitScene()
                else:
                    l = self.manager.current_line()
                    if l: self.manager.char_index = len(l.get('text', ''))

    def _handle_flash(self, data):
        self.flash_color = data.get('color', (255, 255, 255))
        self.flash_timer = 0.15

    def _handle_shake(self, data):
        self.shake_amount = data.get('intensity', 15)

    def _handle_wait(self, data):
        self.flash_timer = data.get('seconds', 0.2)
        
    def _start_music(self, path):
        """Inicia la música de fondo."""
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.12)
        except Exception as e:
            print(f"No se pudo cargar la música: {e}")

    def _stop_music(self):
        """Detiene la música de fondo con un fadeout suave."""
        pygame.mixer.music.fadeout(500)