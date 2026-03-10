import json
import os

class ScreenSettings:

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

class Colors:

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    LIGHT_RED = (255, 80, 80)
    GRAY_180 = (180, 180, 180)
    GRAY_120 = (120, 120, 120)

class GUISettings:

    BUTTON_SIZE = (160, 48)
    FONT_SIZE = 20
    FONT_TEXT = "Arial"

class GameSettings:
    
    MATCH_DURATION = 180 # in seconds

class DialogueAnimationController:
    POP   = "pop"
    SLIDE = "slide"

    _mode = POP  # default

    @classmethod
    def set_mode(cls, mode):
        if mode in (cls.POP, cls.SLIDE):
            cls._mode = mode

    @classmethod
    def get_mode(cls):
        return cls._mode

    @classmethod
    def is_pop(cls):
        return cls._mode == cls.POP


class DialogueSpeedController:
    NORMAL = 1.0
    FAST   = 3.0

    _speed = NORMAL  # default

    @classmethod
    def set_fast(cls):
        cls._speed = cls.FAST

    @classmethod
    def set_normal(cls):
        cls._speed = cls.NORMAL

    @classmethod
    def get_speed(cls):
        return cls._speed

    @classmethod
    def is_fast(cls):
        return cls._speed == cls.FAST


class VolumeController:
    # Control de volumen separado para Música y SFX
    _music_volume = 0.7  # Default music volume (70%)
    _sfx_volume = 0.8    # Default SFX volume (80%)

    @classmethod
    def initialize_from_settings(cls):
        saved_volumes = SettingsManager.get_volumes()
        if saved_volumes:
            cls._music_volume = saved_volumes.get('music', 0.7)
            cls._sfx_volume = saved_volumes.get('sfx', 0.8)
        cls._update_mixer()

    @classmethod
    def set_music_volume(cls, volume):
        cls._music_volume = max(0.0, min(1.0, volume))
        cls._update_mixer()

    @classmethod
    def set_sfx_volume(cls, volume):
        cls._sfx_volume = max(0.0, min(1.0, volume))
        # Actualizar volumen de todos los canales SFX en tiempo real
        try:
            import pygame
            if pygame.mixer.get_init():
                for i in range(pygame.mixer.get_num_channels()):
                    pygame.mixer.Channel(i).set_volume(cls._sfx_volume)
        except:
            pass

    @classmethod
    def get_music_volume(cls):
        return cls._music_volume

    @classmethod
    def get_sfx_volume(cls):
        return cls._sfx_volume

    @classmethod
    def get_current_volume(cls):
        """Para compatibilidad con código existente"""
        return cls._music_volume
    
    @classmethod
    def _update_mixer(cls):
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(cls._music_volume)
        except:
            pass
    
    @classmethod
    def apply_sfx_volume(cls, sound):
        if sound:
            try:
                sound.set_volume(cls._sfx_volume)
            except:
                pass
        return sound


class SettingsManager:
    SETTINGS_FILE = "game_settings.json"

    @classmethod
    def get_settings(cls):
        if os.path.exists(cls.SETTINGS_FILE):
            try:
                with open(cls.SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @classmethod
    def save_settings(cls, settings):
        try:
            with open(cls.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception:
            return False

    @classmethod
    def get_volume(cls):
        settings = cls.get_settings()
        return settings.get('volume', 0.5)
    
    @classmethod
    def get_volumes(cls):
        """Get music and SFX volumes"""
        settings = cls.get_settings()
        volumes = settings.get('volumes', {})
        # Also restore dialogue speed
        dialogue_fast = settings.get('dialogue_fast', False)
        if dialogue_fast:
            DialogueSpeedController.set_fast()
        else:
            DialogueSpeedController.set_normal()
        dialogue_anim = settings.get('dialogue_anim', DialogueAnimationController.POP)
        DialogueAnimationController.set_mode(dialogue_anim)
        return {
            'music': volumes.get('music', 0.7),
            'sfx': volumes.get('sfx', 0.8),
        }
    
    @classmethod
    def save_volumes(cls, music_vol, sfx_vol):
        """Save music and SFX volumes"""
        settings = cls.get_settings()
        settings['volumes'] = {
            'music': music_vol,
            'sfx': sfx_vol,
        }
        settings['dialogue_fast'] = DialogueSpeedController.is_fast()
        settings['dialogue_anim'] = DialogueAnimationController.get_mode()
        return cls.save_settings(settings)