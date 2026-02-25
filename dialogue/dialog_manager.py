import json
import os

class DialogManager:
    def __init__(self, json_path, global_speed=40):
        self.json_path = json_path
        self.global_speed = global_speed
        self._load()
        self.current = 0
        self.char_index = 0
        self.done = False

    def _load(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.lines = self.data.get('lines', [])

    def current_line(self):
        if self.current < len(self.lines):
            return self.lines[self.current]
        return None

    def update(self, dt):
        line = self.current_line()
        if line is None:
            self.done = True
            return
        speed = line.get('speed', self.global_speed)
        self.char_index += speed * dt
        if self.char_index >= len(line.get('text','')):
            self.char_index = len(line.get('text',''))

    def get_shown_text(self):
        line = self.current_line()
        if not line:
            return ''
        return line.get('text','')[:int(self.char_index)]

    def is_line_complete(self):
        line = self.current_line()
        if not line:
            return True
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