import pygame
import random

class DialogueSoundPlayer:
    def __init__(self, config, volume=0.08):
        """
        config: Diccionario que mapea nombres de personajes a LISTAS de objetos Sound.
        Ejemplo: { "Tenazas": [SFXAssets.dialog_1], "default": [SFXAssets.dialog_2] }
        """
        self.character_sounds = {}
        self.default_sounds = []
        
        for char_name, sounds in config.items():
            # Nos aseguramos de que cada sonido tenga el volumen correcto
            for snd in sounds:
                if snd:
                    snd.set_volume(volume)
            
            if char_name == "default":
                self.default_sounds = [s for s in sounds if s is not None]
            else:
                self.character_sounds[char_name] = [s for s in sounds if s is not None]

        self.enabled = True
        self.letter_count = 0
        self.interval = 3

    def set_interval_by_speed(self, speed):
        """Ajusta la cadencia del sonido según la velocidad del texto."""
        if speed <= 15: 
            self.interval = 2
        elif speed <= 40: 
            self.interval = 3
        else: 
            self.interval = 5

    def reset(self):
        """Reinicia el contador al empezar una nueva línea de diálogo."""
        self.letter_count = 0

    def play_check(self, char, speaker_name):
        """Reproduce un sonido si el carácter es válido y toca por intervalo."""
        if not self.enabled:
            return

        # Elegir la lista de sonidos según el personaje, o el default si no existe
        sounds_to_play = self.character_sounds.get(speaker_name, self.default_sounds)
        
        if not sounds_to_play:
            return

        # Solo procesamos si el carácter no es un espacio en blanco
        if char and char.strip():
            # Controlamos la frecuencia para que no suene una ametralladora
            if self.letter_count % self.interval == 0:
                sound = random.choice(sounds_to_play)
                if sound:
                    # maxtime=100 asegura que el "blip" sea corto y no se ensucie el audio
                    sound.play(maxtime=100) 
            
            self.letter_count += 1