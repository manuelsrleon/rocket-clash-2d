import pygame
from settings import ScreenSettings, VolumeController
from scene import *
from pygame.locals import *

class Director:
    
    def __init__(self):
        self.screen = None
        self.scene_stack = []
        self.exit_scene = False
        # Campaign
        self._campaign_scenes = []
        self._campaign_index = 0

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
        # Llamar on_exit en la escena anterior si existe
        if len(self.scene_stack) > 0:
            previous_scene = self.scene_stack[-1]
            if hasattr(previous_scene, 'on_exit'):
                previous_scene.on_exit()
        self.scene_stack.append(scene)

    def apilarEscena(self, scene):
        self.pararEscena()
        self.scene_stack.append(scene)
        
    def _play_main_menu_music(self):
        """Relanza la musica del menu principal si existe en el stack."""
        try:
            from menu import Menu
            from assets_manager import Assets

            remaining = self.scene_stack
            if remaining and isinstance(remaining[0], Menu):
                music_path = Assets.get_music_path("main_menu")
                if music_path:
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(VolumeController.get_music_volume())
                    pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error relanzando musica del menu: {e}")

    @property
    def in_campaign(self):
        return bool(self._campaign_scenes)

    def start_campaign(self, scene_factories):
        """Begin a campaign with a list of scene factory callables."""
        self._campaign_scenes = scene_factories
        self._campaign_index = 0
        if self._campaign_scenes:
            scene = self._campaign_scenes[0]()
            self._campaign_index = 1
            self.apilarEscena(scene)

    def advance_campaign(self):
        """Current campaign scene finished successfully. Pop it and push the next one."""
        if self._campaign_index < len(self._campaign_scenes):
            next_scene = self._campaign_scenes[self._campaign_index]()
            self._campaign_index += 1
            # Pop current, push next
            self.pararEscena()
            if self.scene_stack:
                self.scene_stack.pop()
            self.scene_stack.append(next_scene)
        else:
            # Campaign complete
            self._campaign_scenes = []
            self._campaign_index = 0
            self.exitScene()  # Pop last campaign scene, back to menu
            self._play_main_menu_music()
 
    def fail_campaign(self):
        """Player lost. Abandon campaign and return to main menu."""
        self._campaign_scenes = []
        self._campaign_index = 0
        self.pararEscena()
        # Pop everything except the menu (first scene)
        while len(self.scene_stack) > 1:
            self.scene_stack.pop()
        self._play_main_menu_music()
