import pygame
import random

class DialogueSoundPlayer:
    def __init__(self, config, volume=0.05):
        """
        config: Diccionario estilo { "Ruedaldinho": ["path1"], "Oponente": ["path2"] }
        """
        self.character_sounds = {}
        self.default_sounds = []
        
        for char_name, files in config.items():
            loaded_sounds = []
            for f in files:
                try:
                    snd = pygame.mixer.Sound(f)
                    snd.set_volume(volume)
                    loaded_sounds.append(snd)
                except:
                    print(f"Error cargando sonido para {char_name}: {f}")
            
            if char_name == "default":
                self.default_sounds = loaded_sounds
            else:
                self.character_sounds[char_name] = loaded_sounds

        self.enabled = True
        self.letter_count = 0
        self.interval = 3

    def set_interval_by_speed(self, speed):
        if speed <= 15: self.interval = 2
        elif speed <= 40: self.interval = 3
        else: self.interval = 5

    def reset(self):
        self.letter_count = 0

    def play_check(self, char, speaker_name):
        """Recibe el nombre del que habla para elegir el sonido."""
        if not self.enabled:
            return

        # Elegir la lista de sonidos según el personaje
        sounds_to_play = self.character_sounds.get(speaker_name, self.default_sounds)
        
        if not sounds_to_play:
            return

        if char and char.strip():
            if self.letter_count % self.interval == 0:
                random.choice(sounds_to_play).play(maxtime=100)
            self.letter_count += 1