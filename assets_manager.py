import pygame
from settings import ScreenSettings
import os

# Asset directory paths
BALLS_PATH = "assets/balls"
CARS_PATH = "assets/cars"
GUI_PATH = "assets/gui"
SFX_PATH = "assets/sfx"

def load_image(name, path, scale=None):
    image = pygame.image.load(os.path.join(path, name))
    if scale is not None:
        image = pygame.transform.scale(image, scale)
    return image


def load_sound(name, path):
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    return pygame.mixer.Sound(os.path.join(path, name))


class BallsAssets:
    ball = None

    @classmethod
    def load(cls):
        if cls.ball is None:
            cls.ball = load_image("ball.png", BALLS_PATH, (50, 50))


class CarsAssets:
    car_wheel = None
    player_car = None

    @classmethod
    def load(cls):
        if cls.car_wheel is None:
            cls.car_wheel = load_image("car_wheel.png", CARS_PATH, (100, 50))
        if cls.player_car is None:
            cls.player_car = load_image("player_car.png", CARS_PATH, (140, 70))


class GUIAssets:
    exit_button = None
    play_button = None
    main_menu_bg = None
    main_menu_svg = None

    @classmethod
    def load(cls):
        if cls.exit_button is None:
            cls.exit_button = load_image("exit_button.png", GUI_PATH, (160, 48))
        if cls.play_button is None:
            cls.play_button = load_image("play_button.png", GUI_PATH, (160, 48))
        if cls.main_menu_bg is None:
            cls.main_menu_bg = load_image(
                "main_menu_bg.png",
                GUI_PATH,
                (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT),
            )
        if cls.main_menu_svg is None:
            cls.main_menu_svg = load_image("main_menu.svg", GUI_PATH)


class SFXAssets:
    ball_against_goalpost = None
    car_lowrevs = None
    car_motor_interior = None
    car_touching_ball1 = None
    car_touching_ball2 = None
    car_touching_ball3 = None
    car_touching_ball4 = None
    crash1 = None
    crash2 = None
    crash3 = None
    crowd_hits_besta = None
    publico1 = None
    publico_estadio_cantando = None
    explosion1 = None
    explosion2 = None
    explosion3 = None
    explosion4 = None
    explosion5 = None
    ferrari = None
    motor1 = None
    motor2 = None
    turbo1 = None
    turbo2 = None
    goal1 = None
    goal2 = None
    klaxon1 = None
    klaxon2 = None
    klaxon3 = None
    klaxon4 = None
    klaxon5 = None
    musica2 = None
    musica4 = None
    silbato_corto = None
    silbato_largo = None
    toque_balon = None
    victory_fanfare = None

    @classmethod
    def load(cls):
        if cls.ball_against_goalpost is None:
            cls.ball_against_goalpost = load_sound("ball_against_goalpost.ogg", SFX_PATH)
        if cls.car_lowrevs is None:
            cls.car_lowrevs = load_sound("car_lowrevs.ogg", SFX_PATH)
        if cls.car_motor_interior is None:
            cls.car_motor_interior = load_sound("car_motor_interior.ogg", SFX_PATH)
        if cls.car_touching_ball1 is None:
            cls.car_touching_ball1 = load_sound("car_touching_ball1.ogg", SFX_PATH)
        if cls.car_touching_ball2 is None:
            cls.car_touching_ball2 = load_sound("car_touching_ball2.ogg", SFX_PATH)
        if cls.car_touching_ball3 is None:
            cls.car_touching_ball3 = load_sound("car_touching_ball3.ogg", SFX_PATH)
        if cls.car_touching_ball4 is None:
            cls.car_touching_ball4 = load_sound("car_touching_ball4.ogg", SFX_PATH)
        if cls.crash1 is None:
            cls.crash1 = load_sound("crash1.ogg", SFX_PATH)
        if cls.crash2 is None:
            cls.crash2 = load_sound("crash2.ogg", SFX_PATH)
        if cls.crash3 is None:
            cls.crash3 = load_sound("crash3.ogg", SFX_PATH)
        if cls.crowd_hits_besta is None:
            cls.crowd_hits_besta = load_sound("crowd_hits_besta.ogg", SFX_PATH)
        if cls.publico1 is None:
            cls.publico1 = load_sound("publico1.ogg", SFX_PATH)
        if cls.publico_estadio_cantando is None:
            cls.publico_estadio_cantando = load_sound("publico_estadio cantando.ogg", SFX_PATH)
        if cls.explosion1 is None:
            cls.explosion1 = load_sound("explosion1.ogg", SFX_PATH)
        if cls.explosion2 is None:
            cls.explosion2 = load_sound("explosion2.ogg", SFX_PATH)
        if cls.explosion3 is None:
            cls.explosion3 = load_sound("explosion3.ogg", SFX_PATH)
        if cls.explosion4 is None:
            cls.explosion4 = load_sound("explosion4.ogg", SFX_PATH)
        if cls.explosion5 is None:
            cls.explosion5 = load_sound("explosion5.ogg", SFX_PATH)
        if cls.ferrari is None:
            cls.ferrari = load_sound("ferrari.ogg", SFX_PATH)
        if cls.motor1 is None:
            cls.motor1 = load_sound("motor1.ogg", SFX_PATH)
        if cls.motor2 is None:
            cls.motor2 = load_sound("motor2.ogg", SFX_PATH)
        if cls.turbo1 is None:
            cls.turbo1 = load_sound("turbo1.ogg", SFX_PATH)
        if cls.turbo2 is None:
            cls.turbo2 = load_sound("turbo2.ogg", SFX_PATH)
        if cls.goal1 is None:
            cls.goal1 = load_sound("goal1.ogg", SFX_PATH)
        if cls.goal2 is None:
            cls.goal2 = load_sound("goal2.ogg", SFX_PATH)
        if cls.klaxon1 is None:
            cls.klaxon1 = load_sound("klaxon1.ogg", SFX_PATH)
        if cls.klaxon2 is None:
            cls.klaxon2 = load_sound("klaxon2.ogg", SFX_PATH)
        if cls.klaxon3 is None:
            cls.klaxon3 = load_sound("klaxon3.ogg", SFX_PATH)
        if cls.klaxon4 is None:
            cls.klaxon4 = load_sound("klaxon4.ogg", SFX_PATH)
        if cls.klaxon5 is None:
            cls.klaxon5 = load_sound("klaxon5.ogg", SFX_PATH)
        if cls.musica2 is None:
            cls.musica2 = load_sound("musica2.ogg", SFX_PATH)
        if cls.musica4 is None:
            cls.musica4 = load_sound("musica4.ogg", SFX_PATH)
        if cls.silbato_corto is None:
            cls.silbato_corto = load_sound("silbato_corto.ogg", SFX_PATH)
        if cls.silbato_largo is None:
            cls.silbato_largo = load_sound("silbato_largo.ogg", SFX_PATH)
        if cls.toque_balon is None:
            cls.toque_balon = load_sound("toque balon.ogg", SFX_PATH)
        if cls.victory_fanfare is None:
            cls.victory_fanfare = load_sound("victory_fanfare.ogg", SFX_PATH)
