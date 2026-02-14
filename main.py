"""Main entry point for the game application.

This module initializes the game director and starts the game with the main menu.
"""

from features.match.scene import MatchScene
from director import Director
from features.menu.scene import Menu

# Legacy global screen variable (not currently used)
screen = None

if __name__ == "__main__":
    # Create the game director (manages scenes and game loop)
    director = Director()

    # Start with the main menu scene
    scene = Menu(director)
    director.appendScene(scene)

    # Run the game
    director.execute()
