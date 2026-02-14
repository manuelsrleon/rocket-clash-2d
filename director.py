import pygame
from settings import ScreenSettings, VolumeController
from scene import *
from pygame.locals import *

class Director:
    
    def __init__(self):
        self.screen = None
        self.scene_stack = []
        self.exit_scene = False

    def init_pygame(self):
        pygame.init()
        pygame.mixer.init(44100, -16, 2, 512)
        self.screen = pygame.display.set_mode(
            (ScreenSettings.SCREEN_WIDTH, ScreenSettings.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("Rocket Clash")
        
        # Initialize volume from saved settings
        VolumeController.initialize_from_settings()

    def buclePygame(self, scene):
        clock = pygame.time.Clock()
        self.exit_scene = False

        pygame.event.clear()

        while not self.exit_scene:
            delta_time = clock.tick(ScreenSettings.FPS)
            events = pygame.event.get()

            for ev in events:
                if ev.type == pygame.QUIT:
                    self.salirPrograma()
                    return

            scene.events(events)
            scene.update(delta_time)

            # Skip rendering if the scene stack is empty (when exiting game)
            if not self.scene_stack:
                continue
            current_scene = self.scene_stack[-1]
            if (hasattr(current_scene, "is_overlay") and current_scene.is_overlay and len(self.scene_stack) > 1):
                previous_scene = self.scene_stack[-2]
                previous_scene.render(self.screen)
            current_scene.render(self.screen)
            pygame.display.flip()

    def ejecutar(self):
        self.init_pygame()
        while len(self.scene_stack) > 0:
            scene = self.scene_stack[len(self.scene_stack) - 1]
            scene.screen = self.screen
            self.buclePygame(scene)
        pygame.quit()

    def pararEscena(self):
        if len(self.scene_stack) > 0:
            scene = self.scene_stack[len(self.scene_stack) - 1]
            if isinstance(scene, PyGameScene):
                self.exit_scene = True
            else:
                raise Exception("Unrecognized scene type")

    def exitScene(self):
        self.pararEscena()
        if len(self.scene_stack) > 0:
            self.scene_stack.pop()

    def salirPrograma(self):
        self.pararEscena()
        self.scene_stack = []

    def cambiarEscena(self, scene):
        self.pararEscena()
        self.scene_stack.append(scene)

    def apilarEscena(self, scene):
        self.pararEscena()
        self.scene_stack.append(scene)
        
