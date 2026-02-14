"""Base scene classes for the game.

Provides abstract base classes that all game scenes inherit from:
- Scene: Generic scene interface
- PyGameScene: Pygame-specific scene implementation
"""

import pygame
from settings import ScreenSettings


class Scene:
    """Abstract base class for all game scenes.

    A scene represents a distinct state or screen in the game
    (e.g., menu, gameplay, settings).

    Attributes:
        director: Reference to the game director managing this scene
    """

    def __init__(self, director):
        """Initialize the scene.

        Args:
            director: The game director instance
        """
        self.director = director

    def update(self, *args):
        """Update scene logic. Must be implemented by subclasses.

        Args:
            *args: Typically includes delta_time (milliseconds since last frame)
        """
        raise NotImplemented("Update method not implemented.")

    def events(self, *args):
        """Handle input events. Must be implemented by subclasses.

        Args:
            *args: Typically includes event_list (list of pygame events)
        """
        raise NotImplemented("Events method not implemented.")

    def render(self, *args):
        """Render the scene. Must be implemented by subclasses.

        Args:
            *args: Typically includes screen (pygame.Surface to render on)
        """
        raise NotImplemented("Render method not implemented.")


class PyGameScene(Scene):
    """Pygame-specific scene implementation.

    Extends Scene with pygame-specific features:
    - Screen surface management (assigned by Director)
    - Overlay rendering support

    Attributes:
        screen: pygame.Surface for rendering (assigned by Director before running)
        is_overlay: If True, the scene below will also be rendered
    """

    def __init__(self, director):
        """Initialize the pygame scene.

        Args:
            director: The game director instance
        """
        Scene.__init__(self, director)
        # The Director is responsible for initializing pygame and the mixer,
        # and for creating the single display surface. Scenes declare a
        # `screen` attribute which the Director will assign before running
        # the scene loop.
        self.screen = None
        # If True, the scene below will also be rendered
        self.is_overlay = False
