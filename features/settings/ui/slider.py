"""Volume slider UI component.

Provides an interactive slider control for adjusting volume with:
- Mouse drag support
- Click-to-position
- Snapping to 10% increments
- Visual feedback (filled bar, draggable handle)
"""

import pygame
from features.settings.constants import (
    SLIDER_WIDTH,
    SLIDER_HEIGHT,
    SLIDER_HANDLE_RADIUS,
    SLIDER_BG_COLOR,
    SLIDER_FG_COLOR,
    SLIDER_HANDLE_COLOR,
    VOLUME_MIN,
    VOLUME_MAX,
)


class VolumeSlider:
    """Interactive slider for volume control.

    Features:
    - Drag handle to adjust volume
    - Click anywhere on bar to jump to position
    - Values snap to 10% increments (0.0, 0.1, 0.2, ..., 1.0)
    - Visual feedback with filled/unfilled portions

    Attributes:
        x, y: Position of slider's top-left corner
        width, height: Slider bar dimensions
        value: Current value (0.0 to 1.0)
        dragging: Whether user is currently dragging
        bg_rect: Background bar rectangle
        handle_x: Current X position of the handle
    """

    def __init__(self, x, y, initial_value=0.5):
        """Initialize the volume slider.

        Args:
            x: X position of slider
            y: Y position of slider
            initial_value: Starting volume (0.0 to 1.0), defaults to 0.5
        """
        self.x = x
        self.y = y
        self.width = SLIDER_WIDTH
        self.height = SLIDER_HEIGHT
        self.value = initial_value  # 0.0 to 1.0
        self.dragging = False

        # Create rectangles for the slider
        self.bg_rect = pygame.Rect(x, y, self.width, self.height)
        self.handle_x = self._value_to_x(self.value)

    def _value_to_x(self, value):
        """Convert value (0.0-1.0) to X position on the slider bar.

        Args:
            value: Volume value between 0.0 and 1.0

        Returns:
            int: X coordinate for handle position
        """
        return self.x + int(value * self.width)

    def _x_to_value(self, x):
        """Convert X position to value (0.0-1.0) with 10% increments.

        Args:
            x: X coordinate on screen

        Returns:
            float: Snapped value (0.0, 0.1, 0.2, ..., 1.0)
        """
        relative_x = max(0, min(x - self.x, self.width))
        raw_value = relative_x / self.width
        # Snap to 10% increments (0.0, 0.1, 0.2, ..., 1.0)
        snapped_value = round(raw_value * 10) / 10
        return snapped_value

    def handle_event(self, event):
        """Handle mouse events for the slider.

        Supports:
        - Left click on handle or bar to start dragging
        - Mouse motion while dragging to adjust value
        - Mouse release to stop dragging

        Args:
            event: pygame event to process
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = event.pos
                # Check if click is on handle or slider bar
                handle_rect = pygame.Rect(
                    self.handle_x - SLIDER_HANDLE_RADIUS,
                    self.y - SLIDER_HANDLE_RADIUS + self.height // 2,
                    SLIDER_HANDLE_RADIUS * 2,
                    SLIDER_HANDLE_RADIUS * 2,
                )
                if handle_rect.collidepoint(
                    mouse_x, mouse_y
                ) or self.bg_rect.collidepoint(mouse_x, mouse_y):
                    self.dragging = True
                    self.handle_x = max(self.x, min(mouse_x, self.x + self.width))
                    self.value = self._x_to_value(self.handle_x)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = event.pos
                self.handle_x = max(self.x, min(mouse_x, self.x + self.width))
                self.value = self._x_to_value(self.handle_x)

    def get_value(self):
        """Get current slider value.

        Returns:
            float: Current volume (0.0 to 1.0)
        """
        return self.value

    def set_value(self, value):
        """Set slider value programmatically.

        Args:
            value: New volume value (0.0 to 1.0), will be clamped to valid range
        """
        self.value = max(VOLUME_MIN, min(value, VOLUME_MAX))
        self.handle_x = self._value_to_x(self.value)

    def render(self, screen):
        """Draw the slider on screen.

        Renders:
        1. Background bar (unfilled portion)
        2. Filled bar (from left to handle position)
        3. Draggable handle (outer and inner circles)

        Args:
            screen: pygame.Surface to render on
        """
        # Draw background bar
        pygame.draw.rect(screen, SLIDER_BG_COLOR, self.bg_rect, border_radius=5)

        # Draw filled portion (from left to handle)
        filled_width = self.handle_x - self.x
        if filled_width > 0:
            filled_rect = pygame.Rect(self.x, self.y, filled_width, self.height)
            pygame.draw.rect(screen, SLIDER_FG_COLOR, filled_rect, border_radius=5)

        # Draw handle (outer circle)
        handle_center = (self.handle_x, self.y + self.height // 2)
        pygame.draw.circle(
            screen, SLIDER_HANDLE_COLOR, handle_center, SLIDER_HANDLE_RADIUS
        )
        # Draw inner circle for better visibility and depth
        pygame.draw.circle(
            screen, SLIDER_FG_COLOR, handle_center, SLIDER_HANDLE_RADIUS - 3
        )
