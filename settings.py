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

    def __init__(self):
        self.current_volume = 0.5  # Default volume (50%)

    def initialize_from_settings(self):
        saved_volume = SettingsManager().get_volume()
        if saved_volume is not None:
            self.current_volume = saved_volume

    def set_volume(self, volume):
        self.current_volume = max(0.0, min(1.0, volume))

    
    def get_current_volume(self):
        return self.current_volume


class SettingsManager:
    SETTINGS_FILE = "game_settings.json"

    
    def get_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    
    def save_settings(self, settings):
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception:
            return False

    
    def get_volume(self):
        settings = self.get_settings()
        return settings.get('volume', 0.5)
