"""Asset management module - handles loading and caching of game resources.

This module provides centralized asset loading for:
- Ball sprites
- Car sprites
- GUI elements and backgrounds
- Sound effects (SFX)

All assets are loaded once at module import time and cached in class attributes.
"""

import pygame
from settings import ScreenSettings
import os

# Asset directory paths
BASE_PATH = os.path.dirname(__file__)
BALLS_PATH = os.path.join(BASE_PATH, "balls")
CARS_PATH = os.path.join(BASE_PATH, "cars")
GUI_PATH = os.path.join(BASE_PATH, "gui")
SFX_PATH = os.path.join(BASE_PATH, "sfx")


def load_image(name, path, scale=None):
    """Load an image from disk and optionally scale it.

    Args:
        name: Filename of the image
        path: Directory path containing the image
        scale: Optional tuple (width, height) to scale the image

    Returns:
        pygame.Surface containing the loaded (and possibly scaled) image
    """
    image = pygame.image.load(os.path.join(path, name))
    if scale is not None:
        image = pygame.transform.scale(image, scale)
    return image


def load_sound(name, path):
    """Load a sound effect from disk.

    Args:
        name: Filename of the sound
        path: Directory path containing the sound

    Returns:
        pygame.mixer.Sound object ready to play
    """
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    return pygame.mixer.Sound(os.path.join(path, name))


class BallsAssets:
    """Container for ball sprite assets."""

    ball = load_image("ball.png", BALLS_PATH, (50, 50))


class CarsAssets:
    """Container for car sprite assets."""

    car_wheel = load_image("car_wheel.png", CARS_PATH, (100, 50))
    # placeholder_car = load_image("placeholder_car.png", CARS_PATH, (120, 60))
    player_car = load_image("player_car.png", CARS_PATH, (140, 70))


class GUIAssets:
    """Container for GUI image assets (buttons, backgrounds, etc.)."""

    exit_button = load_image("exit_button.png", GUI_PATH, (160, 48))
    play_button = load_image("play_button.png", GUI_PATH, (160, 48))
    main_menu_bg = load_image(
        "main_menu_bg.png",
        GUI_PATH,
        (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT),
    )
    main_menu_svg = load_image("main_menu.svg", GUI_PATH)


class SFXAssets:
    """Container for sound effect assets.

    Includes sounds for:
    - Ball interactions
    - Car engines and movements
    - Collisions and explosions
    - Crowd reactions
    - Goals and game events
    - Music tracks
    """

    # Ball sounds
    ball_against_goalpost = load_sound("ball_against_goalpost.ogg", SFX_PATH)
    # Car sounds
    car_lowrevs = load_sound("car_lowrevs.ogg", SFX_PATH)
    car_motor_interior = load_sound("car_motor_interior.ogg", SFX_PATH)
    car_touching_ball1 = load_sound("car_touching_ball1.ogg", SFX_PATH)
    car_touching_ball2 = load_sound("car_touching_ball2.ogg", SFX_PATH)
    car_touching_ball3 = load_sound("car_touching_ball3.ogg", SFX_PATH)
    car_touching_ball4 = load_sound("car_touching_ball4.ogg", SFX_PATH)

    # Collision sounds
    crash1 = load_sound("crash1.ogg", SFX_PATH)
    crash2 = load_sound("crash2.ogg", SFX_PATH)
    crash3 = load_sound("crash3.ogg", SFX_PATH)

    # Crowd reactions
    crowd_hits_besta = load_sound("crowd_hits_besta.ogg", SFX_PATH)
    publico1 = load_sound("publico1.ogg", SFX_PATH)
    publico_estadio_cantando = load_sound("publico_estadio cantando.ogg", SFX_PATH)

    # Explosion sounds
    explosion1 = load_sound("explosion1.ogg", SFX_PATH)
    explosion2 = load_sound("explosion2.ogg", SFX_PATH)
    explosion3 = load_sound("explosion3.ogg", SFX_PATH)
    explosion4 = load_sound("explosion4.ogg", SFX_PATH)
    explosion5 = load_sound("explosion5.ogg", SFX_PATH)

    # Engine sounds
    ferrari = load_sound("ferrari.ogg", SFX_PATH)
    motor1 = load_sound("motor1.ogg", SFX_PATH)
    motor2 = load_sound("motor2.ogg", SFX_PATH)
    turbo1 = load_sound("turbo1.ogg", SFX_PATH)
    turbo2 = load_sound("turbo2.ogg", SFX_PATH)

    # Goal sounds
    goal1 = load_sound("goal1.ogg", SFX_PATH)
    goal2 = load_sound("goal2.ogg", SFX_PATH)

    # Horn/klaxon sounds
    klaxon1 = load_sound("klaxon1.ogg", SFX_PATH)
    klaxon2 = load_sound("klaxon2.ogg", SFX_PATH)
    klaxon3 = load_sound("klaxon3.ogg", SFX_PATH)
    klaxon4 = load_sound("klaxon4.ogg", SFX_PATH)
    klaxon5 = load_sound("klaxon5.ogg", SFX_PATH)

    # Music tracks
    musica2 = load_sound("musica2.ogg", SFX_PATH)
    musica4 = load_sound("musica4.ogg", SFX_PATH)

    # Whistle sounds
    silbato_corto = load_sound("silbato_corto.ogg", SFX_PATH)
    silbato_largo = load_sound("silbato_largo.ogg", SFX_PATH)

    # Ball touch sound
    toque_balon = load_sound("toque balon.ogg", SFX_PATH)

    # Victory sound
    victory_fanfare = load_sound("victory_fanfare.ogg", SFX_PATH)
