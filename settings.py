"""Global game settings and constants.

This module contains configuration classes for:
- Screen/display settings
- Common color definitions
- GUI/interface settings
"""


class ScreenSettings:
    """Display and rendering configuration."""

    SCREEN_WIDTH = 800  # Window width in pixels
    SCREEN_HEIGHT = 600  # Window height in pixels
    FPS = 60  # Target frames per second


class Colors:
    """Common color constants in RGB format."""

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)


class GUISettings:
    """GUI element default settings."""

    BUTTON_SIZE = (160, 48)  # Default button dimensions (width, height)
    FONT_SIZE = 20  # Default font size
    FONT_TEXT = "Arial"  # Default font family
