import json
import os

class DialogueManager:
    def __init__(self, json_path):
        self.json_path = json_path
        self.data = {}
        self.lines = []
        self.characters = {}
        self.speed_multiplier = 1.0
        self.current = 0
        self.char_index = 0
        self.done = False
        
        # Lógica de pausas
        self.pause_timer = 0.0
        self.punctuation_pauses = {
            ".": 0.5,
            ",": 0.2,
            "!": 0.4,
            "?": 0.4,
            "...": 0.6  
        }
        
        self._load()

    def _load(self):
        """Carga el JSON y limpia los datos para el Assets Manager."""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.lines = self.data.get('lines', [])
        self.characters = self.data.get('characters', {})
        self.base_speed = self.data.get('base_speed', 20)

    def set_speed_multiplier(self, multiplier):
        self.speed_multiplier = multiplier

    def current_line(self):
        if self.current < len(self.lines):
            return self.lines[self.current]
        return None

    def update(self, dt):
        line = self.current_line()
        if not line:
            return

        if self.pause_timer > 0:
            self.pause_timer -= dt
            return

        text = line.get('text', '')
        text_len = len(text)
        
        if self.char_index < text_len:
            old_idx = int(self.char_index)
            speed = self.base_speed * self.speed_multiplier
            self.char_index += speed * dt
            new_idx = int(self.char_index)

            # Comprobar puntuación para pausas
            if new_idx > old_idx and new_idx <= text_len:
                char_actual = text[old_idx]
                
                # Prioridad a puntos suspensivos
                if char_actual == "." and text[old_idx:old_idx+3] == "...":
                    self.pause_timer = self.punctuation_pauses["..."]
                    self.char_index = old_idx + 3 
                elif char_actual in self.punctuation_pauses:
                    self.pause_timer = self.punctuation_pauses[char_actual]
                    self.char_index = old_idx + 1

        if self.char_index >= text_len:
            self.char_index = text_len

    def get_shown_text(self):
        line = self.current_line()
        return line.get('text','')[:int(self.char_index)] if line else ''

    def is_line_complete(self):
        line = self.current_line()
        if not line: return True
        return int(self.char_index) >= len(line.get('text',''))

    def advance(self):
        """Avanza de línea y resetea estados."""
        if not self.is_line_complete():
            self.char_index = len(self.current_line().get('text',''))
            return 'continued'
        
        self.current += 1
        self.char_index = 0
        self.pause_timer = 0
        
        if self.current >= len(self.lines):
            self.done = True
            return 'finished'
        return 'next'

    # --- NUEVAS FUNCIONES DE APOYO PARA LA ESCENA ---

    def get_current_speaker_state(self):
        """
        Retorna el estado del personaje definido en la línea.
        Si no hay estado, devuelve 'idle' por defecto.
        """
        line = self.current_line()
        if line:
            return line.get('state', 'idle')
        return 'idle'

    def get_current_events(self):
        """Retorna la lista de eventos definidos en la línea."""
        line = self.current_line()
        if not line: return []
        evts = line.get('events') or line.get('event') or []
        return evts if isinstance(evts, list) else [evts]