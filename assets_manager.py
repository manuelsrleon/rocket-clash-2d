import pygame
from settings import ScreenSettings
import os

# --- RUTAS DE DIRECTORIOS ---
BASE_PATH = os.path.dirname(__file__)
BALLS_PATH = os.path.join(BASE_PATH, "assets", "balls")
CARS_PATH = os.path.join(BASE_PATH, "assets", "cars")
GUI_PATH = os.path.join(BASE_PATH, "assets", "gui")
SFX_PATH = os.path.join(BASE_PATH, "assets", "sfx")
BACKGROUNDS_PATH = os.path.join(BASE_PATH, "assets", "backgrounds")
PORTRAITS_PATH = os.path.join(BASE_PATH, "assets", "portraits")
STADIUMS_PATH = os.path.join(BASE_PATH, "assets", "stadiums")

class Assets:
    """
    Gestor centralizado. Carga assets solo cuando se piden (Lazy Loading).
    Permite importar escenas antes de inicializar Pygame.
    """
    _images_cache = {}
    _sounds_cache = {}

    # --- DICCIONARIO DE IMÁGENES  ---
    _IMAGE_DATA = {
        # Fondos
        "background": ("background.png", BACKGROUNDS_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        "bulldozer_background": ("bulldozer_background.png", BACKGROUNDS_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        "credits_background": ("credits_background.png", BACKGROUNDS_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        "stadium1_bg": ("stadium1_bg.png", STADIUMS_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        "stadium2_bg": ("stadium2_bg.png", STADIUMS_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        "stadium3_bg": ("stadium3_bg.png", STADIUMS_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        
        # Portraits
        "Bulldozer": ("Bulldozer.png", PORTRAITS_PATH, None),
        "MotoMoto": ("MotoMoto.png", PORTRAITS_PATH, None),
        "Jenny": ("Jenny.png", PORTRAITS_PATH, None),
        "Ruedaldinho": ("Ruedaldinho.png", PORTRAITS_PATH, None),
        "tenazas_1": ("Tenazas_1.png", PORTRAITS_PATH, None),
        "tenazas_2": ("Tenazas_2.png", PORTRAITS_PATH, None),

        # Balls & Cars
        "ball": ("ball.png", BALLS_PATH, (50, 50)),
        "car_wheel": ("car_wheel.png", CARS_PATH, (100, 50)),
        "player_car": ("player_car.png", CARS_PATH, (140, 70)),

        # GUI
        "exit_button": ("exit_button.png", GUI_PATH, (160, 48)),
        "play_button": ("play_button.png", GUI_PATH, (160, 48)),
        "main_menu_bg": ("Main_Background.png", GUI_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)),
        "main_menu_svg": ("main_menu.svg", GUI_PATH, None),
        "settings_bg": ("settings_background.png", GUI_PATH, (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT))
    }

    # --- DICCIONARIO DE SONIDOS ---
    _SOUND_DATA = {
        # Ball sounds
        "ball_against_goalpost": "ball_against_goalpost.ogg",
        "toque_balon": "toque balon.ogg",
        
        # Car & Engine
        "car_lowrevs": "car_lowrevs.ogg",
        "car_motor_interior": "car_motor_interior.ogg",
        "car_touching_ball1": "car_touching_ball1.ogg",
        "car_touching_ball2": "car_touching_ball2.ogg",
        "car_touching_ball3": "car_touching_ball3.ogg",
        "car_touching_ball4": "car_touching_ball4.ogg",
        "ferrari": "ferrari.ogg",
        "motor1": "motor1.ogg",
        "motor2": "motor2.ogg",
        "turbo1": "turbo1.ogg",
        "turbo2": "turbo2.ogg",

        # Collisions & Explosions
        "crash1": "crash1.ogg",
        "crash2": "crash2.ogg",
        "crash3": "crash3.ogg",
        "explosion1": "explosion1.ogg",
        "explosion2": "explosion2.ogg",
        "explosion3": "explosion3.ogg",
        "explosion4": "explosion4.ogg",
        "explosion5": "explosion5.ogg",

        # Crowd & Ambience
        "crowd_hits_besta": "crowd_hits_besta.ogg",
        "publico1": "publico1.ogg",
        "publico_estadio_cantando": "publico_estadio cantando.ogg",

        # Goals & Whistles
        "goal1": "goal1.ogg",
        "goal2": "goal2.ogg",
        "silbato_corto": "silbato_corto.ogg",
        "silbato_largo": "silbato_largo.ogg",

        # Horns
        "klaxon1": "klaxon1.ogg",
        "klaxon2": "klaxon2.ogg",
        "klaxon3": "klaxon3.ogg",
        "klaxon4": "klaxon4.ogg",
        "klaxon5": "klaxon5.ogg",

        # Dialogue specific
        "dialog_1": "dialog_1.ogg",
        "dialog_2": "dialog_2.ogg",
        "dialog_text_1": "dialog_text_1.ogg",
        "dialog_text_2": "dialog_text_2.ogg",
        "dialog_text_3": "dialog_text_3.ogg",
        "dialog_text_4": "dialog_text_4.ogg"
    }
    
    _MUSIC_DATA = {
        "musica2": "musica2.ogg",
        "musica4": "musica4.ogg",
        "intro_bg_theme": "intro_bg_theme.ogg",
        "match_bg_theme_1": "match_bg_theme_1.ogg",
        "match1_bg_playing_theme": "match_1_bg_music_hydeouts_points.ogg",
        "match3_bg_playing_theme": "match_3_bg_music.ogg",
        "match_bg_theme_2": "match_bg_theme_2.ogg",
        "match_bg_theme_3": "match_bg_theme_3.ogg",
        "victory": "victory.ogg",
        "final_victory": "final_victory_theme.ogg",
        "main_menu": "main_menu_bg_theme.ogg"
        
    }

    @staticmethod
    def get_image(key):
        if key in Assets._images_cache:
            return Assets._images_cache[key]

        if key in Assets._IMAGE_DATA:
            name, path, scale = Assets._IMAGE_DATA[key]
            try:
                img = pygame.image.load(os.path.join(path, name))
                if pygame.display.get_surface():
                    img = img.convert_alpha()
                if scale:
                    img = pygame.transform.scale(img, scale)
                Assets._images_cache[key] = img
                return img
            except Exception as e:
                print(f"Error cargando imagen {key}: {e}")

        # Fallback Magenta
        surf = pygame.Surface((50, 50))
        surf.fill((255, 0, 255))
        return surf

    @staticmethod
    def get_sound(key):
        if key in Assets._sounds_cache:
            return Assets._sounds_cache[key]

        if key in Assets._SOUND_DATA:
            filename = Assets._SOUND_DATA[key]
            # Si el mixer no está listo, lo intentamos inicializar
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                except:
                    return None
            
            try:
                sound_path = os.path.join(SFX_PATH, filename)
                sound = pygame.mixer.Sound(sound_path)
                Assets._sounds_cache[key] = sound
                return sound
            except Exception as e:
                print(f"Error cargando sonido {key}: {e}")
        return None
    

    @staticmethod
    def get_music_path(key):
        filename = Assets._MUSIC_DATA.get(key)
        if filename:
            return os.path.join(SFX_PATH, filename)
        return None
