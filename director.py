"""Game director module - manages the game loop and scene stack.

The Director class is responsible for:
- Initializing pygame and the display
- Managing a stack of scenes
- Running the main game loop
- Handling scene transitions
"""

import pygame
from settings import ScreenSettings
from features.common.scene import *
from pygame.locals import *
from features.settings.lib.volume import VolumeController


class Director:
    """Main game director that manages scenes and the game loop.

    Attributes:
        screen: The main pygame display surface
        scene_stack: Stack of active scenes (last item is the currently active scene)
        exit_scene: Flag to signal when to exit the current scene's main loop
    """

    def __init__(self):
        """Initialize the director with empty scene stack."""
        self.screen = None
        self.scene_stack = []
        self.exit_scene = False

    def init_pygame(self):
        """Initialize pygame, the display window, and audio mixer.

        Sets up:
        - Pygame core systems
        - Audio mixer with standard settings (44.1kHz, stereo, 512 buffer)
        - Display window with configured dimensions
        - Window caption
        - Volume from saved settings
        """
        pygame.init()
        pygame.mixer.init(44100, -16, 2, 512)
        self.screen = pygame.display.set_mode(
            (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("Rocket Clash")

        # Initialize volume from saved settings
        VolumeController.initialize_from_settings()

    def mainLoop(self, scene):
        """Run the main game loop for the given scene.

        Args:
            scene: The scene to run in this loop

        The loop handles:
        - Frame timing (locked to configured FPS)
        - Event processing
        - Scene updates
        - Rendering (including overlay support)
        - Global quit event handling
        """
        clock = pygame.time.Clock()
        self.exit_scene = False

        pygame.event.clear()

        while not self.exit_scene:
            # Control frame rate and get delta time in milliseconds
            delta_time = clock.tick(ScreenSettings.FPS)
            events = pygame.event.get()

            # Handle global quit immediately to close the whole program
            for ev in events:
                if ev.type == pygame.QUIT:
                    # Clear stack and request stop so execute() will exit
                    self.exitGame()
                    return

            # Pass events to the current scene
            scene.events(events)

            # Update scene logic
            scene.update(delta_time)

            # Skip rendering if the scene stack is empty (when exiting game)
            if not self.scene_stack:
                continue

            # If this is an overlay scene, render the scene below first
            current_scene = self.scene_stack[-1]
            if (
                hasattr(current_scene, "is_overlay")
                and current_scene.is_overlay
                and len(self.scene_stack) > 1
            ):
                previous_scene = self.scene_stack[-2]
                previous_scene.render(self.screen)
            current_scene.render(self.screen)
            pygame.display.flip()

    def execute(self):
        """Start the game and run until all scenes are closed.

        This is the main entry point after initializing the director.
        It runs each scene on the stack until the stack is empty,
        then cleanly shuts down pygame.
        """
        self.init_pygame()
        while len(self.scene_stack) > 0:
            scene = self.scene_stack[len(self.scene_stack) - 1]
            # Ensure the scene uses the single display surface created by the Director
            scene.screen = self.screen
            self.mainLoop(scene)

        pygame.quit()

    def stopScene(self):
        """Signal the current scene's main loop to exit.

        Sets the exit_scene flag which will cause the mainLoop to terminate.

        Raises:
            Exception: If the current scene is not a PyGameScene instance
        """
        if len(self.scene_stack) > 0:
            scene = self.scene_stack[len(self.scene_stack) - 1]
            if isinstance(scene, PyGameScene):
                self.exit_scene = True
            else:
                raise Exception("Unrecognized scene type")

    def exitScene(self):
        """Exit the current scene and remove it from the stack."""
        self.stopScene()

        if len(self.scene_stack) > 0:
            self.scene_stack.pop()

    def exitGame(self):
        """Exit the entire game by clearing all scenes from the stack."""
        self.stopScene()
        self.scene_stack = []

    def changeScene(self, scene):
        """Replace the current scene with a new one.

        Args:
            scene: The new scene to switch to
        """
        self.stopScene()
        self.scene_stack.append(scene)

    def appendScene(self, scene):
        """Add a new scene on top of the current one.

        The current scene is paused and the new scene becomes active.
        When the new scene exits, control returns to the previous scene.

        Args:
            scene: The new scene to add to the stack
        """
        self.stopScene()
        self.scene_stack.append(scene)
