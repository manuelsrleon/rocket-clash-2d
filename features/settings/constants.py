"""Constants for the settings feature.

Defines visual appearance and layout for the settings screen:
- Colors and background
- Volume slider configuration
- Font sizes
- Element positioning
"""

from settings import Colors

# Background
BACKGROUND_COLOR = (30, 30, 30)  # Dark gray background

# Volume settings
VOLUME_MIN = 0.0  # Minimum volume (muted)
VOLUME_MAX = 1.0  # Maximum volume (100%)
VOLUME_STEP = 0.1  # Volume adjustment increment (10%)
DEFAULT_VOLUME = 0.5  # Starting volume (50%)

# Slider dimensions
SLIDER_WIDTH = 300  # Slider bar width in pixels
SLIDER_HEIGHT = 10  # Slider bar height in pixels
SLIDER_HANDLE_RADIUS = 15  # Draggable handle radius

# Slider colors
SLIDER_BG_COLOR = (100, 100, 100)  # Unfilled portion (gray)
SLIDER_FG_COLOR = (50, 150, 255)  # Filled portion (blue)
SLIDER_HANDLE_COLOR = Colors.WHITE  # Draggable handle (white)

# Text styling
TITLE_FONT_SIZE = 48  # "Settings" title size
LABEL_FONT_SIZE = 24  # Labels and percentage text size
TEXT_COLOR = Colors.WHITE

# Layout positioning (Y coordinates)
TITLE_Y = 50  # Title position from top
VOLUME_SLIDER_Y = 200  # Slider vertical position
SLIDER_LABEL_OFFSET = 40  # Distance between slider and labels
SAVE_BUTTON_Y = 400  # Save button vertical position
