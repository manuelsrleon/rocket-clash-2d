import os
import pygame
import random
from scene import PyGameScene
from assets_manager import Assets
from dialogue.dialog_manager import DialogueManager
from dialogue.dialog_ui import DialogueUI
from dialogue.dialogue_sound_player import DialogueSoundPlayer
from settings import DialogueSpeedController

class DialogueScene(PyGameScene):
    def __init__(self, director, json_path):
        super().__init__(director)
        self.screen = getattr(director, "screen", None) or pygame.display.get_surface()
        sw, sh = self.screen.get_size()

        # --- CONFIGURACIÓN VISUAL ---
        self.font = pygame.font.Font(None, 28)
        self.fixed_sprite_y = 40
        self.margin_side = 10
        self.sprite_to_bubble_gap = 10
        self.bubble_gap = 8

        # --- GESTIÓN DE DIÁLOGOS ---
        self.manager = DialogueManager(json_path)
        self.history = []
        
        num_chars = len(self.manager.data.get('characters', {}))
        # Factor global que afecta a todos (puedes ajustarlo si quieres miniaturas)
        self.scale_factor = 0.75 if num_chars > 1 else 1.0

        # --- CARGA DINÁMICA ---
        bg_key = self.manager.data.get('background', 'background')
        self.bg = Assets.get_image(bg_key)
        self.character_sprites = self._load_characters()
        
        # Calculamos el punto de inicio de las burbujas basado en el sprite más alto cargado
        # para evitar que el texto pise a los personajes
        max_h = 0
        for char in self.character_sprites.values():
            max_h = max(max_h, char["display_size"][1])
        
        self.start_bubbles_y = self.fixed_sprite_y + max_h + self.sprite_to_bubble_gap

        # --- SISTEMA DE SONIDO DE VOCES ---
        sound_config = {
            "Tenazas": [Assets.get_sound("dialog_1")],
            "Ruedaldinho": [
                Assets.get_sound("dialog_text_1"), 
                Assets.get_sound("dialog_text_2"), 
                Assets.get_sound("dialog_text_3"), 
                Assets.get_sound("dialog_text_4")
            ],
            "default": [Assets.get_sound("dialog_2")] 
        }
        self.audio_player = DialogueSoundPlayer(sound_config)
        self.audio_player.set_interval_by_speed(self.manager.base_speed)

        # Aplicar velocidad de diálogo según la configuración guardada
        self.manager.set_speed_multiplier(DialogueSpeedController.get_speed())
        
        # --- MÚSICA ---
        self.bgm_key = self.manager.data.get('music')
        self.music_started = False

        # --- ESTADO DE EFECTOS ---
        self.effects_queue = []
        self.flash_timer = 0
        self.flash_color = None
        self.shake_offset = pygame.Vector2(0, 0)
        self.shake_amount = 0
        
        # NUEVO: Flag para controlar la pausa final
        self.is_exiting = False

        self.effect_handlers = {
            "flash": self._handle_flash, 
            "shake": self._handle_shake, 
            "wait": self._handle_wait
        }

        # Iniciamos la escena apareciendo desde negro
        self.fade_from_black()
        self._spawn_current_bubble()

    def _load_characters(self):
        sprites = {}
        chars_data = self.manager.data.get('characters', {})
        for side_key, data in chars_data.items():
            name = data.get('name')
            if not name: continue
            
            # Obtenemos la imagen base para conocer su tamaño real
            portraits = data.get('portraits', {"idle": data.get('portrait_key')})
            base_img = Assets.get_image(portraits.get("idle"))
            
            # Si no hay "size" en el JSON, usamos el tamaño original del archivo
            size_data = data.get('size', base_img.get_size())
            
            char_w = int(size_data[0] * self.scale_factor)
            char_h = int(size_data[1] * self.scale_factor)
            
            sprites[name] = {
                "side": side_key,
                "display_size": (char_w, char_h)
            }
            
            portraits = data.get('portraits', {"idle": data.get('portrait_key')})
            
            for state, asset_key in portraits.items():
                if asset_key:
                    img = Assets.get_image(asset_key)
                    img = pygame.transform.scale(img, (char_w, char_h))
                    sprites[name][state] = img
            
            if "idle" in sprites[name] and "talk" not in sprites[name]:
                sprites[name]["talk"] = sprites[name]["idle"]
        return sprites

    def update(self, dt):
        # 1. Actualizar el fundido
        self.update_fade(dt)
        
        # Si ya estamos en negro total y esperando a salir, procesamos solo FX
        if self.is_exiting and self.fade_alpha >= 255:
            self._update_fx_logic(dt / 1000.0)
            return

        # 2. Si estamos fundiendo a negro por haber terminado, permitimos que el render 
        # siga dibujando el último estado pero detenemos la lógica de avance.
        if self.fade_mode == "IN" and self.fade_alpha > 250:
            return

        if not self.music_started:
            if self.bgm_key:
                path = Assets.get_music_path(self.bgm_key)
                if path and os.path.exists(path):
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.12)
                    pygame.mixer.music.play(loops=-1)
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
        
        self._update_fx_logic(dt_sec)

    def _update_fx_logic(self, dt_sec):
        # 1. Procesar cola de efectos si no hay un temporizador activo
        if self.flash_timer <= 0 and self.effects_queue:
            eff = self.effects_queue.pop(0)
            handler = self.effect_handlers.get(eff.get('type'))
            if handler: handler(eff)
            
        # 2. Control del tiempo de flash o espera
        if self.flash_timer > 0:
            self.flash_timer -= dt_sec
            if self.flash_timer <= 0: 
                self.flash_color = None
                # SI ESTAMOS SALIENDO y termina el wait, cerramos la escena
                if self.is_exiting and not self.effects_queue:
                    self.director.exitScene()
                
        # 3. AUTO-AVANCE: Si la cola está vacía y la línea actual no tiene texto
        if not self.is_exiting and self.flash_timer <= 0 and not self.effects_queue:
            line = self.manager.current_line()
            if line and not line.get('text', '').strip():
                result = self.manager.advance()
                if result == 'next':
                    self._spawn_current_bubble()
                elif result == 'finished':
                    self._start_exit_transition()
            
        # 4. Lógica de Shake
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

        # Definimos el "suelo" donde apoyan los personajes
        suelo_y = self.start_bubbles_y - self.sprite_to_bubble_gap

        # Render de personajes con posicionamiento dinámico por ancho y alineado a la base (suelo)
        for char_name, char_info in self.character_sprites.items():
            is_speaking = (char_name == speaker_now)
            side = char_info.get("side", "middle")
            c_w, c_h = char_info["display_size"]
            
            # Calculamos la posición Y para que la base del sprite toque el suelo
            dynamic_y = suelo_y - c_h
            
            # Mapa de posiciones recalculado con dynamic_y
            pos_map = {
                "left":   (self.margin_side, dynamic_y),
                "middle": ((sw // 2) - (c_w // 2), dynamic_y),
                "right":  (sw - c_w - self.margin_side, dynamic_y)
            }
            
            pos_key = "middle" if num_chars_in_scene <= 1 else side
            draw_pos = pos_map.get(pos_key, pos_map["middle"])
            
            state = "talk" if (is_speaking and not self.manager.is_line_complete()) else "idle"
            img = char_info.get(state) or char_info.get("idle")
            
            if img:
                if num_chars_in_scene > 1 and not is_speaking:
                    shaded = img.copy()
                    shaded.fill((120, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    temp_surf.blit(shaded, draw_pos)
                else:
                    temp_surf.blit(img, draw_pos)

        current_y = self.start_bubbles_y
        for i, bubble in enumerate(self.history):
            is_last_in_history = (i == len(self.history) - 1)
            txt = bubble.full_text
            if not self.is_exiting and is_last_in_history:
                txt = self.manager.get_shown_text()

            show_hint = is_last_in_history and not self.is_exiting
            
            # Si solo hay un personaje, centramos el texto, si no, a la izquierda
            draw_x = 50
            if num_chars_in_scene <= 1:
                # Intentamos centrar la burbuja relativo al ancho del único personaje
                char_name = list(self.character_sprites.keys())[0]
                c_w = self.character_sprites[char_name]["display_size"][0]
                draw_x = (sw // 2) - (c_w // 2)
            
            y_inc = bubble.draw(temp_surf, current_y, txt, draw_x, is_last=show_hint)
            current_y += y_inc + self.bubble_gap

        screen.blit(temp_surf, (self.shake_offset.x, self.shake_offset.y))
        
        if self.flash_color and self.flash_timer > 0:
            f = pygame.Surface(screen.get_size())
            f.fill(self.flash_color)
            f.set_alpha(150)
            screen.blit(f, (0, 0))

        self.draw_fade(screen)

    def events(self, events):
        if self.fade_mode == "IN" or self.is_exiting:
            return

        for event in events:
            if event.type == pygame.QUIT: 
                self.director.salirPrograma()
            
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.manager.is_line_complete():
                    result = self.manager.advance()
                    if result == 'next': 
                        self._spawn_current_bubble()
                    elif result == 'finished': 
                        self._start_exit_transition()
                else:
                    l = self.manager.current_line()
                    if l: self.manager.char_index = len(l.get('text', ''))

    def _start_exit_transition(self):
        """Bloquea la escena y funde a negro manteniendo el último texto."""
        if self.is_exiting: return
        
        self.is_exiting = True
        self._stop_all_audio()
        
        self.fade_speed = 100 

        def al_terminar_negro():
            self.effects_queue.append({"type": "wait", "seconds": 2.0})
            
        self.fade_to_black(callback=al_terminar_negro)

    def _spawn_current_bubble(self):
        line = self.manager.current_line()
        if not line: return
        
        # Encolar eventos
        self.effects_queue.extend(self.manager.get_current_events())
        self.audio_player.reset()
        
        text_content = line.get('text', '').strip()
        
        # SI NO HAY TEXTO: Salimos sin crear UI (update() se encargará de avanzar).
        if not text_content:
            return

        # SI HAY TEXTO: Lógica normal de creación de burbuja
        new_speaker = line.get('speaker')
        new_side = line.get('side', 'left')
        
        if self.history:
            last_bubble = self.history[-1]
            last_speaker = getattr(last_bubble, 'name', None) or getattr(last_bubble, 'speaker', None)
            if new_speaker != last_speaker:
                self.history = []

        new_bubble = DialogueUI(new_speaker, text_content, None, new_side, self.font)
        
        # Cálculo de altura
        current_y_cursor = self.start_bubbles_y
        for b in self.history:
            current_y_cursor += b.get_expected_height() + self.bubble_gap
        
        if current_y_cursor + new_bubble.get_expected_height() > (self.screen.get_height() - self.bubble_gap):
            self.history = []

        self.history.append(new_bubble)

    def _handle_flash(self, data):
        self.flash_color = data.get('color', (255, 255, 255))
        self.flash_timer = data.get('seconds', 0.15)

    def _handle_shake(self, data):
        self.shake_amount = data.get('intensity', 15)

    def _handle_wait(self, data):
        self.flash_timer = data.get('seconds', 0.2)

    def _stop_all_audio(self):
        pygame.mixer.music.fadeout(1000)