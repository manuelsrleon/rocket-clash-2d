import json
import os

class DialogManager:
    def __init__(self, json_path):
        self.json_path = json_path
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
        """Carga el JSON y configura la velocidad base de la escena."""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.lines = self.data.get('lines', [])
        self.characters = self.data.get('characters', {})
        
        # Leemos 'base_speed' de la raíz del JSON. Si no existe, usamos 20 como fallback.
        self.base_speed = self.data.get('base_speed', 20)

    def set_speed_multiplier(self, multiplier):
        """Ajusta el multiplicador global (desde ajustes del juego)."""
        self.speed_multiplier = multiplier

    def current_line(self):
        """Retorna el diccionario de la línea actual o None si terminó."""
        if self.current < len(self.lines):
            return self.lines[self.current]
        return None

    def update(self, dt):
        """Avanza el índice de caracteres con soporte para pausas de puntuación."""
        line = self.current_line()
        if line is None:
            self.done = True
            return

        # Si hay una pausa activa por puntuación, no avanzamos
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

            # Comprobar si hemos pasado por un carácter de puntuación
            if new_idx > old_idx and new_idx <= text_len:
                # Miramos el carácter que acabamos de "escribir"
                char_actual = text[old_idx]
                
                # Caso especial: Puntos suspensivos (...)
                # Si hay tres puntos seguidos, activamos la pausa larga y saltamos los puntos
                if char_actual == "." and text[old_idx:old_idx+3] == "...":
                    self.pause_timer = self.punctuation_pauses["..."]
                    self.char_index = old_idx + 3 # Saltamos los 3 puntos para que no repita pausa
                
                # Caso general: punto, coma, etc.
                elif char_actual in self.punctuation_pauses:
                    self.pause_timer = self.punctuation_pauses[char_actual]
                    # Ajustamos el índice justo después del signo
                    self.char_index = old_idx + 1

        # Limitar al largo del texto
        if self.char_index >= text_len:
            self.char_index = text_len

    def get_shown_text(self):
        """Retorna el fragmento de texto que debe mostrarse actualmente."""
        line = self.current_line()
        if not line:
            return ''
        return line.get('text','')[:int(self.char_index)]

    def is_line_complete(self):
        """Indica si se ha terminado de escribir la línea actual."""
        line = self.current_line()
        if not line: return True
        return int(self.char_index) >= len(line.get('text',''))

    def advance(self):
        """Avanza a la siguiente línea, reseteando el timer de pausa."""
        if not self.is_line_complete():
            self.char_index = len(self.current_line().get('text',''))
            return 'continued'
        
        self.current += 1
        self.char_index = 0
        self.pause_timer = 0 # Reset de pausa al cambiar de línea
        
        if self.current >= len(self.lines):
            self.done = True
            return 'finished'
        return 'next'
    
    def is_finished(self):
        """Indica si la escena ha llegado al final de todas las líneas."""
        return self.done or self.current >= len(self.lines)

    def get_current_events(self):
        """Retorna lista de eventos (shake, flash, etc) de la línea actual."""
        line = self.current_line()
        if not line:
            return []

        evts = line.get('events') or line.get('event')
        if evts is None:
            return []
        
        if isinstance(evts, list):
            return evts
        else:
            return [evts]