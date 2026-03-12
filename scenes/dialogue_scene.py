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
        self.fixed_sprite_y = 10 
        self.margin_side = 10
        self.sprite_to_bubble_gap = 10
        self.bubble_gap = 20 

        # --- GESTIÓN DE DIÁLOGOS ---
        self.manager = DialogueManager(json_path)
        self.history = []
        
        chars_data = self.manager.data.get('characters', {})
        num_chars = len(chars_data)
        self.scale_factor = 0.75 if num_chars > 1 else 1.0

        # --- CARGA DINÁMICA ---
        bg_key = self.manager.data.get('background', 'background')
        self.bg = Assets.get_image(bg_key)
        self.character_sprites = self._load_characters()
        
        # --- CÁLCULO DE LÍMITES DINÁMICOS ---
        max_c_h = 0
        for char_info in self.character_sprites.values():
            max_c_h = max(max_c_h, char_info["display_size"][1])
        
        self.char_ground_y = sh - 20
        max_char_top_y = self.char_ground_y - max_c_h
        
        self.dialogue_ground_y = max_char_top_y - self.sprite_to_bubble_gap
        self.intro_dialogue_start_y = self.fixed_sprite_y + max_c_h + self.sprite_to_bubble_gap

        # --- SISTEMA DE SONIDO ---
        sound_config = {
            "Tenazas": [Assets.get_sound("dialog_1")],
            "Ruedaldinho": [
                Assets.get_sound("dialog_text_1"), Assets.get_sound("dialog_text_2"), 
                Assets.get_sound("dialog_text_3"), Assets.get_sound("dialog_text_4")
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
        self.is_exiting = False

        self.effect_handlers = {"flash": self._handle_flash, "shake": self._handle_shake, "wait": self._handle_wait}

        self.fade_from_black()
        self._spawn_current_bubble()

    def _load_characters(self):
        sprites = {}
        chars_data = self.manager.data.get('characters', {})
        for side_key, data in chars_data.items():
            name = data.get('name')
            if not name: continue
            portraits = data.get('portraits', {"idle": data.get('portrait_key')})
            base_img = Assets.get_image(portraits.get("idle"))
            size_data = data.get('size', base_img.get_size())
            char_w = int(size_data[0] * self.scale_factor)
            char_h = int(size_data[1] * self.scale_factor)
            sprites[name] = {"side": side_key, "display_size": (char_w, char_h)}
            for state, asset_key in portraits.items():
                if asset_key:
                    img = Assets.get_image(asset_key)
                    img = pygame.transform.scale(img, (char_w, char_h))
                    sprites[name][state] = img
            if "idle" in sprites[name] and "talk" not in sprites[name]:
                sprites[name]["talk"] = sprites[name]["idle"]
        return sprites

    def _spawn_current_bubble(self):
        line = self.manager.current_line()
        if not line: return
        self.effects_queue.extend(self.manager.get_current_events())
        self.audio_player.reset()
        text_content = line.get('text', '').strip()
        if not text_content: return

        new_speaker = line.get('speaker')
        new_side = line.get('side', 'left')
        num_chars = len(self.character_sprites)
        
        temp_bubble = DialogueUI(new_speaker, text_content, None, new_side, self.font)
        new_h = temp_bubble.get_expected_height()

        if num_chars <= 1:
            total_h_existing = sum(b.get_expected_height() + self.bubble_gap for b in self.history)
            if self.intro_dialogue_start_y + total_h_existing + new_h > (self.screen.get_height() - 40):
                self.history = []
        else:
            if self.history and new_speaker != self.history[-1].name:
                self.history = []
            total_h_existing = sum(b.get_expected_height() + self.bubble_gap for b in self.history)
            if (self.dialogue_ground_y - (total_h_existing + new_h)) < 20:
                self.history = []

        self.history.append(temp_bubble)

    def update(self, dt):
        self.update_fade(dt)
        if self.is_exiting and self.fade_alpha >= 255:
            self._update_fx_logic(dt / 1000.0)
            return
        if self.fade_mode == "IN" and self.fade_alpha > 250: return

        if not self.music_started:
            if self.bgm_key:
                path = Assets.get_music_path(self.bgm_key)
                if path and os.path.exists(path):
                    pygame.mixer.music.load(path); pygame.mixer.music.set_volume(0.12); pygame.mixer.music.play(loops=-1)
            self.music_started = True

        dt_sec = dt / 1000.0
        old_idx = int(self.manager.char_index)
        sm = getattr(self.director, 'settings_manager', None)
        if sm: self.manager.set_speed_multiplier(sm.get_dialogue_speed_multiplier())
        
        self.manager.update(dt_sec)
        new_idx = int(self.manager.char_index)
        
        if new_idx > old_idx:
            line = self.manager.current_line()
            if line:
                text = line.get('text', '')
                speaker_name = line.get('speaker', 'default')
                for i in range(old_idx, new_idx):
                    if i < len(text): self.audio_player.play_check(text[i], speaker_name)

        for b in self.history: b.update_anim(dt_sec)
        self._update_fx_logic(dt_sec)

    def _update_fx_logic(self, dt_sec):
        if self.flash_timer <= 0 and self.effects_queue:
            eff = self.effects_queue.pop(0)
            handler = self.effect_handlers.get(eff.get('type'))
            if handler: handler(eff)
        if self.flash_timer > 0:
            self.flash_timer -= dt_sec
            if self.flash_timer <= 0: 
                self.flash_color = None
                if self.is_exiting and not self.effects_queue:
                    if self.director.in_campaign:
                        self.director.advance_campaign()
                    else:
                        self.director.exitScene()
                
        if not self.is_exiting and self.flash_timer <= 0 and not self.effects_queue:
            line = self.manager.current_line()
            if line and not line.get('text', '').strip():
                result = self.manager.advance()
                if result == 'next': self._spawn_current_bubble()
                elif result == 'finished': self._start_exit_transition()
        if self.shake_amount > 0:
            amt = int(self.shake_amount)
            self.shake_offset.x = random.randint(-amt, amt); self.shake_offset.y = random.randint(-amt, amt)
            self.shake_amount -= 60 * dt_sec
        else: self.shake_offset = pygame.Vector2(0, 0)

    def render(self, screen):
        sw, sh = screen.get_size()
        temp_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        temp_surf.blit(self.bg, (0, 0))

        current_line = self.manager.current_line()
        speaker_now = current_line.get('speaker') if current_line else None
        num_chars_in_scene = len(self.character_sprites)
        is_intro = (num_chars_in_scene <= 1)

        # 1. PERSONAJES
        if is_intro: suelo_personajes_y = self.fixed_sprite_y
        else: suelo_personajes_y = self.char_ground_y

        for char_name, char_info in self.character_sprites.items():
            is_speaking = (char_name == speaker_now)
            side = char_info.get("side", "middle")
            c_w, c_h = char_info["display_size"]
            dynamic_y = suelo_personajes_y if is_intro else suelo_personajes_y - c_h
            pos_map = {"left": (self.margin_side, dynamic_y), "middle": ((sw // 2) - (c_w // 2), dynamic_y), "right": (sw - c_w - self.margin_side, dynamic_y)}
            draw_pos = pos_map.get("middle" if is_intro else side, pos_map["middle"])
            state = "talk" if (is_speaking and not self.manager.is_line_complete()) else "idle"
            img = char_info.get(state) or char_info.get("idle")
            if img:
                if not is_intro and not is_speaking:
                    shaded = img.copy(); shaded.fill((120, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    temp_surf.blit(shaded, draw_pos)
                else: temp_surf.blit(img, draw_pos)

        # 2. DIÁLOGOS
        if is_intro:
            current_y = self.intro_dialogue_start_y
            for i, bubble in enumerate(self.history):
                is_last = (i == len(self.history) - 1)
                # FIX: Si estamos saliendo, forzamos texto completo en la última burbuja
                if is_last:
                    txt = bubble.full_text if self.is_exiting else self.manager.get_shown_text()
                else:
                    txt = bubble.full_text
                
                char_name = list(self.character_sprites.keys())[0]
                c_w = self.character_sprites[char_name]["display_size"][0]
                draw_x = (sw // 2) - (c_w // 2)
                y_inc = bubble.draw(temp_surf, current_y, txt, draw_x, is_last=(is_last and not self.is_exiting), is_intro=True)
                current_y += y_inc + self.bubble_gap
        else:
            cursor_y = self.dialogue_ground_y
            for i in range(len(self.history) - 1, -1, -1):
                bubble = self.history[i]
                is_last = (i == len(self.history) - 1)
                txt = bubble.full_text if (is_last and self.is_exiting) else (self.manager.get_shown_text() if is_last else bubble.full_text)
                h = bubble.get_expected_height()
                draw_y = cursor_y - h
                bubble.draw(temp_surf, draw_y, txt, 50, is_last=(is_last and not self.is_exiting), is_intro=False)
                cursor_y -= (h + self.bubble_gap)

        screen.blit(temp_surf, (self.shake_offset.x, self.shake_offset.y))
        if self.flash_color and self.flash_timer > 0:
            f = pygame.Surface(screen.get_size()); f.fill(self.flash_color); f.set_alpha(150); screen.blit(f, (0, 0))
        self.draw_fade(screen)

    def events(self, events):
        if self.fade_mode == "IN" or self.is_exiting: return
        for event in events:
            if event.type == pygame.QUIT: self.director.salirPrograma()
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.manager.is_line_complete():
                    result = self.manager.advance()
                    if result == 'next': self._spawn_current_bubble()
                    elif result == 'finished': self._start_exit_transition()
                else:
                    l = self.manager.current_line()
                    if l: self.manager.char_index = len(l.get('text', ''))

    def _start_exit_transition(self):
        if self.is_exiting: return
        self.is_exiting = True; self._stop_all_audio(); self.fade_speed = 100 
        self.fade_to_black(callback=lambda: self.effects_queue.append({"type": "wait", "seconds": 2.0}))

    def _handle_flash(self, data): self.flash_color = data.get('color', (255, 255, 255)); self.flash_timer = data.get('seconds', 0.15)
    def _handle_shake(self, data): self.shake_amount = data.get('intensity', 15)
    def _handle_wait(self, data): self.flash_timer = data.get('seconds', 0.2)
    def _stop_all_audio(self): pygame.mixer.music.fadeout(1000)