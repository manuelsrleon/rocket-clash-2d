# Project Architecture Documentation

## Overview

This document describes the feature-based architecture used in this pygame project. The goal is to organize code by features rather than by technical layers, making the codebase more maintainable, scalable, and easier to understand.

## Core Principles

1. **Feature-Driven Organization**: Each distinct game feature lives in its own isolated folder
2. **Standardized Structure**: Common file naming patterns across features
3. **Self-Contained Features**: Features should be as independent as possible
4. **Centralized Assets**: All game assets are managed from a single top-level location

## Directory Structure

```
proyecto/
├── main.py                          # Application entry point
├── director.py                      # Game director/state manager
├── settings.py                      # Global settings
├── ARCHITECTURE.md                  # This file
├── README.md                        # Project documentation
│
├── features/                        # All game features
│   ├── common/                      # Shared components across features
│   │   ├── ui/                      # Reusable UI components
│   │   │   ├── base_widgets.py      # Base widget classes
│   │   │   ├── buttons.py           # Common button components
│   │   │   └── dialogs.py           # Dialog boxes
│   │   ├── utils/                   # Utility functions
│   │   │   ├── math_helpers.py      # Math utilities
│   │   │   └── timing.py            # Time-related utilities
│   │   └── constants.py             # Global constants used across features
│   │
│   ├── menu/
│   │   ├── scene.py                # Scene implementation
│   │   ├── constants.py            # Feature-specific constants
│   │   ├── ui/                     # UI components
│   │   │   ├── buttons.py
│   │   │   └── widgets.py
│   │   └── lib/                    # Feature utilities
│   │       └── helpers.py
│   │
│   ├── match/
│   │   ├── scene.py
│   │   ├── constants.py
│   │   ├── entities/               # Game entities
│   │   │   ├── car.py
│   │   │   └── ball.py
│   │   ├── physics/                # Physics logic
│   │   │   └── collision.py
│   │   └── ui/
│   │       └── scoreboard.py
│   │
│   ├── settings/
│   │   ├── scene.py
│   │   ├── constants.py
│   │   └── ui/
│   │       └── controls.py
│   │
│   └── ... (other features)
│
└── assets/                          # Centralized asset management
    ├── assets_manager.py           # Asset loading and caching
    ├── gui_elements.py             # Reusable GUI components
    ├── balls/                      # Ball sprites
    ├── cars/                       # Car sprites
    ├── gui/                        # GUI images
    └── sfx/                        # Sound effects
```

## Feature Folder Structure

### Standard Files

Each feature folder should follow this pattern:

#### Required Files

- **`scene.py`**: Main scene implementation for the feature
  - Contains the scene class that handles game logic, rendering, and events
  - Each feature has exactly one `scene.py` file
  - When importing, use aliases to avoid name conflicts:
    ```python
    from features.menu.scene import Menu
    from features.match.scene import MatchScene
    from features.settings.scene import SettingsScene
    ```

- **`constants.py`**: Feature-specific constants
  - Colors, dimensions, timing values, configuration
  - Example values: `BUTTON_WIDTH = 200`, `MENU_BACKGROUND_COLOR = (50, 50, 50)`

#### Optional Files

- **`README.md`**: Feature documentation
  - Purpose of the feature
  - Key components and their responsibilities
  - Usage examples
  - Dependencies on other features

### Standard Subfolders

Features can organize their code using these common subfolders:

- **`ui/`**: User interface components
  - Buttons, labels, widgets specific to this feature
  - Layout managers

- **`lib/`**: Utility functions and helpers
  - Helper functions used within the feature
  - Algorithms and data processing

- **`entities/`**: Game entities (if applicable)
  - Player, enemies, items, etc.

- **`physics/`**: Physics and collision logic
  - Movement, collision detection, physics simulation

- **`ai/`**: AI behavior (if applicable)
  - Decision making, pathfinding

### Naming Conventions

1. **Scene Files**: `scene.py`
   - Each feature has exactly one `scene.py` file
   - Import with aliases to avoid conflicts: `from features.menu.scene import Menu`
   - The scene class name should be descriptive (e.g., `Menu`, `MatchScene`, `SettingsScene`)

2. **Constants Files**: `constants.py`
   - Each feature has one `constants.py` file
   - Contains only constants (UPPER_CASE naming)
   - Import as: `from features.menu.constants import BUTTON_WIDTH`

3. **Subfolders**: Lowercase, descriptive names
   - `ui/`, `lib/`, `entities/`, `physics/`, `ai/`

4. **Simplicity**: Keep filenames simple and consistent
   - ✅ `menu/scene.py`, `match/scene.py`, `settings/scene.py`
   - ✅ `menu/constants.py`, `match/constants.py`
   - ❌ `menu/menu_scene.py` (redundant feature name prefix)

## Assets Management

### Asset Organization

All game assets are stored in the top-level `assets/` folder, separate from features:

```
assets/
├── assets_manager.py      # Singleton asset manager
├── gui_elements.py        # Reusable GUI components
├── balls/                 # Ball sprites and animations
├── cars/                  # Car sprites and animations
├── gui/                   # GUI images, buttons, icons
├── fonts/                 # Font files
├── sfx/                   # Sound effects
└── music/                 # Background music
```

### Asset Manager

The `assets_manager.py` provides centralized access to all game assets:

```python
# Features access assets through the manager
from assets.assets_manager import AssetsManager

# In feature code:
car_sprite = AssetsManager.get_car_sprite("red_car")
menu_button = AssetsManager.get_gui_element("start_button")
```

**Benefits:**
- Single loading point for assets
- Caching to avoid duplicate loads
- Easy to swap assets globally
- Clear separation of code and resources

## Benefits of This Architecture

### 1. **Modularity**
- Features are self-contained and can be developed independently
- Easier to add, remove, or modify features without affecting others

### 2. **Maintainability**
- Clear organization makes it easy to find specific functionality
- Related code is grouped together
- Reduces cognitive load when working on a specific feature

### 3. **Scalability**
- New features follow the same pattern
- Team members can work on different features with minimal conflicts
- Easy to onboard new developers

### 4. **Testing**
- Features can be tested in isolation
- Clear boundaries make it easier to write unit tests
- Mocking dependencies is straightforward

### 5. **Reusability**
- Common utilities can be shared across features
- Asset manager provides consistent access to resources
- UI components can be reused where appropriate

## Example Feature: Match

Here's what a complete feature might look like:

```
features/match/
├── scene.py                    # Main match scene
├── constants.py                # Match-specific constants
├── README.md                   # Match feature documentation
├── entities/
│   ├── car.py                  # Car entity with physics
│   ├── ball.py                 # Ball entity
│   └── goal.py                 # Goal zones
├── physics/
│   ├── collision.py            # Collision detection
│   └── movement.py             # Movement calculations
├── ui/
│   ├── scoreboard.py           # Score display
│   ├── timer.py                # Match timer
│   └── pause_menu.py           # Pause overlay
└── lib/
    ├── field_helpers.py        # Field-related utilities
    └── replay_system.py        # Replay functionality
```

## Best Practices

1. **Keep Features Independent**: Minimize dependencies between features
2. **Use the Asset Manager**: Always access assets through the manager
3. **Document Public APIs**: If a feature exposes functionality to others, document it
4. **Follow Naming Conventions**: Consistency makes the codebase predictable
5. **One Responsibility Per File**: Keep files focused on a single purpose
6. **Group Related Items**: Use subfolders when a feature has multiple related components

## Common Patterns

### Scene Communication

Features often need to communicate (e.g., menu starting a match):

```python
# In menu/scene.py
def handle_start_clicked(self):
    self.director.change_scene("match")  # Director handles transitions
```

### Sharing Data Between Features

Use the director or a shared state manager:

```python
# In settings/scene.py
def save_settings(self):
    self.director.game_settings.update(self.settings)

# In match/scene.py
def __init__(self, director):
    self.settings = director.game_settings
```

### Reusable Components

Place truly reusable components in the assets folder or the `features/common/` folder:

```
assets/
└── gui_elements.py          # Buttons, labels used everywhere

# Or for non-asset shared code:
features/common/
├── scene.py                 # Base Scene classes
├── node.py                  # Node system
├── ui/
│   └── base_widgets.py      # Base UI classes
└── utils/
    └── math_helpers.py      # Math utilities
```
