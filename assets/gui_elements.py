"""GUI elements module - reusable UI components.

Provides base classes for building interactive user interfaces:
- GUIElement: Base class for all UI elements
- Button: Interactive button with hover effects
- GUIScreen: Container for managing collections of GUI elements
"""

import pygame
from settings import Colors, GUISettings
from assets.assets_manager import SFXAssets
from pygame.locals import *
from features.settings.lib.volume import VolumeController


class GUIElement:
    """Base class for all GUI elements.

    Provides basic functionality for positioning and interaction detection.
    Subclasses must implement render() and action() methods.

    Attributes:
        screen: Reference to the parent screen/container
        rect: pygame.Rect defining the element's position and size
    """

    def __init__(self, screen, rectangle):
        """Initialize the GUI element.

        Args:
            screen: Parent screen containing this element
            rectangle: pygame.Rect defining position and size
        """
        self.screen = screen
        self.rect = rectangle

    def setPosition(self, position):
        """Set the element's position.

        Args:
            position: Tuple (x, y) for the bottom-left corner
        """
        (posX, posY) = position
        self.rect.left = posX
        self.rect.bottom = posY

    def positionInElement(self, position):
        """Check if a position is within this element's bounds.

        Args:
            position: Tuple (x, y) to check

        Returns:
            bool: True if position is inside the element
        """
        (posX, posY) = position
        return (
            (posX >= self.rect.left)
            and (posX <= self.rect.right)
            and (posY >= self.rect.top)
            and (posY <= self.rect.bottom)
        )

    def render(self):
        """Render the element. Must be implemented by subclasses."""
        raise NotImplemented("Render method not implemented")

    def action(self):
        """Execute the element's action. Must be implemented by subclasses."""
        raise NotImplemented("Action method not implemented")


class Button(GUIElement):
    """Interactive button with hover effects and text.

    Features:
    - Hover state with color change
    - Customizable text and font
    - Border rendering
    - Click sound effects (volume-aware)

    Attributes:
        hover: bool indicating if mouse is over the button
        text: Button label text
        base_rect: Original rect for rendering (independent of GUIElement.rect)
    """

    def __init__(
        self,
        screen,
        position=(0, 0),
        size=GUISettings.BUTTON_SIZE,
        text=None,
        font_name=GUISettings.FONT_TEXT,
        font_size=GUISettings.FONT_SIZE,
    ):
        """Initialize a button.

        Args:
            screen: Parent screen containing this button
            position: Tuple (x, y) for button position
            size: Tuple (width, height) for button dimensions
            text: Optional text label for the button
            font_name: Font family name
            font_size: Font size in points
        """
        self.screen = screen
        self.hover = False
        self._converted = False
        # non-image button: use a rect, optional text and font
        w, h = size
        rect = pygame.Rect(0, 0, w, h)
        GUIElement.__init__(self, screen, rect)
        self.setPosition(position)
        self.base_rect = self.rect.copy()
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self._font = None
        self.color = Colors.WHITE
        self.border_color = Colors.BLACK
        self.hover_color = Colors.YELLOW

    def render(self, screen):
        """Render the button with hover effects and text.

        Args:
            screen: pygame.Surface to render on
        """
        # Use hover color if mouse is over button, otherwise use normal color
        color = self.hover_color if self.hover else self.color
        pygame.draw.rect(screen, color, self.base_rect)
        pygame.draw.rect(screen, self.border_color, self.base_rect, 2)

        if self.text:
            # Lazy load font on first render
            if self._font is None:
                try:
                    self._font = pygame.font.SysFont(self.font_name, self.font_size)
                except Exception:
                    pygame.font.init()
                    self._font = pygame.font.SysFont(self.font_name, self.font_size)

            # Render text centered on button
            label_surf = self._font.render(self.text, True, self.border_color)
            label_rect = label_surf.get_rect(center=self.base_rect.center)
            screen.blit(label_surf, label_rect)

    def isHoverInButton(self, position):
        """Update hover state based on mouse position.

        Args:
            position: Tuple (x, y) of mouse position
        """
        self.hover = self.positionInElement(position)


class GUIScreen:
    """Container for managing a collection of GUI elements.

    Handles:
    - Event distribution to child elements
    - Background image rendering
    - Click detection and action triggering
    - Hover state updates

    Attributes:
        menu: Reference to parent menu/scene
        image: Optional background image
        GUIElements: List of GUI elements to manage
        animations: List of active animations (future use)
    """

    def __init__(self, menu, image=None):
        """Initialize a GUI screen.

        Args:
            menu: Parent menu/scene
            image: Optional background image (pygame.Surface)
        """
        self.menu = menu
        self.image = image
        self.GUIElements = []
        self.animations = []

    def events(self, event_list):
        """Process input events for all GUI elements.

        Handles:
        - Mouse button down: Record which element was clicked
        - Mouse button up: Trigger action if release is on same element
        - Mouse motion: Update hover states

        Args:
            event_list: List of pygame events to process
        """
        for event in event_list:
            # Track which element was clicked on mouse down
            if event.type == MOUSEBUTTONDOWN:
                self.clickElement = None
                for GUIElement in self.GUIElements:
                    if GUIElement.positionInElement(event.pos):
                        self.GUIElementClick = GUIElement

            # Trigger action only if mouse down and up happened on same element
            if event.type == MOUSEBUTTONUP:
                for GUIElement in self.GUIElements:
                    if GUIElement.positionInElement(event.pos):
                        if GUIElement == self.GUIElementClick:
                            # Play click sound with current volume
                            sound = pygame.mixer.Sound.play(SFXAssets.silbato_corto)
                            sound.set_volume(VolumeController.get_current_volume())
                            GUIElement.action()

            # Update hover states for visual feedback
            if event.type == MOUSEMOTION:
                for GUIElement in self.GUIElements:
                    GUIElement.isHoverInButton(event.pos)

    def render(self, screen):
        """Render the background image and all GUI elements.

        Args:
            screen: pygame.Surface to render on
        """
        # Draw background image if present
        if self.image is not None:
            try:
                screen.blit(self.image, self.image.get_rect())
            except Exception:
                pass

        # Draw all GUI elements on top
        for GUIElement in self.GUIElements:
            GUIElement.render(screen)
