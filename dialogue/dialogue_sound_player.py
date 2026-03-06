import pygame
import random

class DialogueSoundPlayer:
    def __init__(self, sound_files, volume=0.15):
        self.sounds = []
        for f in sound_files:
            try:
                snd = pygame.mixer.Sound(f)
                snd.set_volume(volume)
                self.sounds.append(snd)
            except:
                print(f"No se pudo cargar: {f}")
        
        self.enabled = True
        self.letter_count = 0
        self.interval = 3  # Por defecto suena cada 3 letras 

    def set_interval_by_speed(self, speed):
        """Ajusta el intervalo según la velocidad del texto."""
        if speed <= 15: self.interval = 2   # Lento: suena más seguido
        elif speed <= 40: self.interval = 3 # Normal
        else: self.interval = 5             # Rápido: suena menos para no saturar

    def reset(self):
        self.letter_count = 0

    def play_check(self, char):
        """Lógica principal del script: decide si se reproduce un sonido al mostrar un carácter."""
        if not self.enabled or not self.sounds:
            return

        # Ignorar espacios y saltos de línea (char.strip())
        if char and char.strip():
            if self.letter_count % self.interval == 0:
                random.choice(self.sounds).play(maxtime=100)
            self.letter_count += 1