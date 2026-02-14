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

class GUISettings:

    BUTTON_SIZE = (160, 48)
    FONT_SIZE = 20
    FONT_TEXT = "Arial"


class VolumeController:

    _current_volume = 0.5  # Default volume (50%)

    @classmethod
    def initialize_from_settings(cls):
        saved_volume = SettingsManager.get_volume()
        if saved_volume is not None:
            cls._current_volume = saved_volume

    @classmethod
    def set_volume(cls, volume):
        cls._current_volume = max(0.0, min(1.0, volume))

    @classmethod
    def get_current_volume(cls):
        return cls._current_volume


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
