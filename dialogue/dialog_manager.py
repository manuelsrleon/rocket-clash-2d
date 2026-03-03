import json
import os

class DialogManager:
    def __init__(self, json_path, global_speed=40):
        self.json_path = json_path
        self.global_speed = global_speed
        self.characters = {}
        self.speed_multiplier = 1.0
        self._load()
        self.current = 0
        self.char_index = 0
        self.done = False

    def _load(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.lines = self.data.get('lines', [])
        self.characters = self.data.get('characters', {})

    def set_speed_multiplier(self, multiplier):
        self.speed_multiplier = multiplier

    def current_line(self):
        if self.current < len(self.lines):
            return self.lines[self.current]
        return None

    def update(self, dt):
        line = self.current_line()
        if line is None:
            self.done = True
            return
        
        # Aplicamos la velocidad base de la línea y el multiplicador global
        base_speed = line.get('speed', self.global_speed)
        speed = base_speed * self.speed_multiplier
        
        self.char_index += speed * dt
        text_len = len(line.get('text',''))
        if self.char_index >= text_len:
            self.char_index = text_len

    def get_shown_text(self):
        line = self.current_line()
        if not line:
            return ''
        return line.get('text','')[:int(self.char_index)]

    def is_line_complete(self):
        line = self.current_line()
        if not line: return True
        return int(self.char_index) >= len(line.get('text',''))

    def advance(self):
        if not self.is_line_complete():
            self.char_index = len(self.current_line().get('text',''))
            return 'continued'
        self.current += 1
        self.char_index = 0
        if self.current >= len(self.lines):
            self.done = True
            return 'finished'
        return 'next'
    
    def is_finished(self):
        line = self.current_line()
        if not line:
            return True
        return self.char_index >= len(line.get('text', ''))

    # =========================================================
    # SANDBOX (Soporte Multi-Evento)
    # =========================================================
    def get_current_events(self):
        """
        Retorna siempre una lista de eventos, incluso si solo hay uno
        o si el JSON usa la clave 'event' en lugar de 'events'.
        """
        line = self.current_line()
        if not line:
            return []

        # Intentamos obtener 'events' (lista) o 'event' (objeto único)
        evts = line.get('events') or line.get('event')

        if evts is None:
            return []
        
        # Si es una lista, la devolvemos. Si es un solo objeto, lo envolvemos en una lista.
        if isinstance(evts, list):
            return evts
        else:
            return [evts]