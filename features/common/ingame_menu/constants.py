"""Constants for the ingame pause menu.

Defines visual appearance settings:
- Overlay transparency and color
- Menu panel dimensions
- Button spacing
- Colors for menu elements
"""

from settings import Colors

# Menu overlay appearance
OVERLAY_ALPHA = 180  # Semi-transparent background (0-255, where 255 is opaque)
OVERLAY_COLOR = (0, 0, 0)  # Black overlay

# Menu dimensions
MENU_WIDTH = 300
MENU_HEIGHT = 350
MENU_PADDING = 20

# Button spacing
BUTTON_SPACING = 15

# Colors
MENU_BG_COLOR = (50, 50, 70)  # Dark blue-gray background
MENU_BORDER_COLOR = Colors.WHITE
TITLE_COLOR = Colors.WHITE
