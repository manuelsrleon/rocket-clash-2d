import pygame
from scene import PyGameScene
from gui_elements import Button
from settings import ScreenSettings, GUISettings, Colors, VolumeController, SettingsManager
from pygame.locals import *

# Settings constants
BACKGROUND_COLOR = (30, 30, 30)
VOLUME_MIN = 0.0
VOLUME_MAX = 1.0
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 10
SLIDER_HANDLE_RADIUS = 15
SLIDER_BG_COLOR = (100, 100, 100)
SLIDER_FG_COLOR = (50, 150, 255)
SLIDER_HANDLE_COLOR = Colors.WHITE
TITLE_FONT_SIZE = 48
LABEL_FONT_SIZE = 24
TEXT_COLOR = Colors.WHITE
TITLE_Y = 50
MUSIC_SLIDER_Y = 150
SFX_SLIDER_Y = 250
SLIDER_LABEL_OFFSET = 40
SAVE_BUTTON_Y = 400

class VolumeSlider:

    def __init__(self, x, y, initial_value=0.5):
        self.x = x
        self.y = y
        self.width = SLIDER_WIDTH
        self.height = SLIDER_HEIGHT
        self.value = initial_value
        self.selected = False

        self.bg_rect = pygame.Rect(x, y, self.width, self.height)
        self.handle_x = self._value_to_x(self.value)

    def _value_to_x(self, value):
        return self.x + int(value * self.width)

    def _x_to_value(self, x):
        relative_x = max(0, min(x - self.x, self.width))
        raw_value = relative_x / self.width
        snapped_value = round(raw_value * 10) / 10
        return snapped_value

    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_LEFT:
                self.value = max(VOLUME_MIN, self.value - 0.1)
                self.handle_x = self._value_to_x(self.value)
            elif event.key == K_RIGHT:
                self.value = min(VOLUME_MAX, self.value + 0.1)
                self.handle_x = self._value_to_x(self.value)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = max(VOLUME_MIN, min(value, VOLUME_MAX))
        self.handle_x = self._value_to_x(self.value)

    def render(self, screen):
        bg_color = SLIDER_FG_COLOR if self.selected else SLIDER_BG_COLOR
        pygame.draw.rect(screen, bg_color, self.bg_rect, border_radius=5)

        filled_width = self.handle_x - self.x
        if filled_width > 0:
            filled_rect = pygame.Rect(self.x, self.y, filled_width, self.height)
            pygame.draw.rect(screen, SLIDER_FG_COLOR, filled_rect, border_radius=5)

        handle_center = (self.handle_x, self.y + self.height // 2)
        pygame.draw.circle(
            screen, SLIDER_HANDLE_COLOR, handle_center, SLIDER_HANDLE_RADIUS
        )
        pygame.draw.circle(screen, SLIDER_FG_COLOR, handle_center, SLIDER_HANDLE_RADIUS - 3)


class SaveButton(Button):

    def __init__(self, screen):
        Button.__init__(
            self,
            screen,
            position=(ScreenSettings.SCREEN_WIDTH // 2, SAVE_BUTTON_Y),
            text="Guardar",
        )
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        self.screen.save_settings()


class SettingsScene(PyGameScene):

    def __init__(self, director):
        super().__init__(director)
        self.title_font = pygame.font.SysFont(GUISettings.FONT_TEXT, TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont(GUISettings.FONT_TEXT, LABEL_FONT_SIZE)
        slider_x = ScreenSettings.SCREEN_WIDTH // 2 - 150

        # Load saved settings
        volumes = SettingsManager.get_volumes()

        # Create music volume slider
        self.music_slider = VolumeSlider(slider_x, MUSIC_SLIDER_Y, volumes['music'])

        # Create SFX volume slider
        self.sfx_slider = VolumeSlider(slider_x, SFX_SLIDER_Y, volumes['sfx'])

        self.save_button = SaveButton(self)

        # Set initial volumes
        VolumeController.set_music_volume(self.music_slider.get_value())
        VolumeController.set_sfx_volume(self.sfx_slider.get_value())

        self.show_save_message = False
        self.save_message_timer = 0

        self.elements = [self.music_slider, self.sfx_slider, self.save_button]
        self.selected_index = 0
        self._update_selection()

    def _update_selection(self):
        self.music_slider.selected = False
        self.sfx_slider.selected = False
        self.save_button.hover = False

        if self.selected_index == 0:
            self.music_slider.selected = True
        elif self.selected_index == 1:
            self.sfx_slider.selected = True
        elif self.selected_index == 2:
            self.save_button.hover = True

    def update(self, delta_time):
        VolumeController.set_music_volume(self.music_slider.get_value())
        VolumeController.set_sfx_volume(self.sfx_slider.get_value())

        if self.show_save_message:
            self.save_message_timer += delta_time
            if self.save_message_timer >= 2000:
                self.show_save_message = False
                self.save_message_timer = 0

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.director.exitScene()
                elif event.key == K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.elements)
                    self._update_selection()
                elif event.key == K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.elements)
                    self._update_selection()
                elif event.key == K_RETURN or event.key == K_KP_ENTER:
                    if self.selected_index == 2:  # Save button
                        self.save_button.action()
                elif event.key == K_LEFT or event.key == K_RIGHT:
                    if self.selected_index == 0:
                        self.music_slider.handle_event(event)
                    elif self.selected_index == 1:
                        self.sfx_slider.handle_event(event)

    def render(self, screen):
        screen.fill(BACKGROUND_COLOR)
        self._render_title(screen)
        self._render_music_section(screen)
        self._render_sfx_section(screen)
        self.save_button.render(screen)
        if self.show_save_message:
            self._render_save_confirmation(screen)
        self._render_instructions(screen)

    def _render_title(self, screen):
        title_text = self.title_font.render("Configuración", True, TEXT_COLOR)
        title_rect = title_text.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, TITLE_Y)
        )
        screen.blit(title_text, title_rect)

    def _render_music_section(self, screen):
        # Music label (left side)
        music_label = self.label_font.render("Música", True, TEXT_COLOR)
        label_rect = music_label.get_rect(
            midleft=(50, MUSIC_SLIDER_Y)
        )
        screen.blit(music_label, label_rect)

        # Music slider (center)
        self.music_slider.render(screen)

        # Music percentage (right side)
        music_percent = int(self.music_slider.get_value() * 100)
        percent_text = self.label_font.render(f"{music_percent}%", True, TEXT_COLOR)
        percent_rect = percent_text.get_rect(
            midright=(ScreenSettings.SCREEN_WIDTH - 50, MUSIC_SLIDER_Y)
        )
        screen.blit(percent_text, percent_rect)

    def _render_sfx_section(self, screen):
        # SFX label (left side)
        sfx_label = self.label_font.render("Efectos", True, TEXT_COLOR)
        label_rect = sfx_label.get_rect(
            midleft=(50, SFX_SLIDER_Y)
        )
        screen.blit(sfx_label, label_rect)

        # SFX slider (center)
        self.sfx_slider.render(screen)

        # SFX percentage (right side)
        sfx_percent = int(self.sfx_slider.get_value() * 100)
        percent_text = self.label_font.render(f"{sfx_percent}%", True, TEXT_COLOR)
        percent_rect = percent_text.get_rect(
            midright=(ScreenSettings.SCREEN_WIDTH - 50, SFX_SLIDER_Y)
        )
        screen.blit(percent_text, percent_rect)

    def _render_save_confirmation(self, screen):
        save_msg = self.label_font.render("¡Configuración guardada!", True, (100, 255, 100))
        save_msg_rect = save_msg.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, SAVE_BUTTON_Y + 60)
        )
        screen.blit(save_msg, save_msg_rect)

    def _render_instructions(self, screen):
        instructions = self.label_font.render(
            "Flechas: Navegar | Izq/Der: Volumen | Enter: Guardar | ESC: Volver", True, (150, 150, 150)
        )
        instructions_rect = instructions.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT - 30)
        )
        screen.blit(instructions, instructions_rect)

    def save_settings(self):
        music_vol = self.music_slider.get_value()
        sfx_vol = self.sfx_slider.get_value()

        # Save to settings
        SettingsManager.save_volumes(music_vol, sfx_vol)

        self.show_save_message = True
        self.save_message_timer = 0

    def _render_save_confirmation(self, screen):
        save_msg = self.label_font.render("¡Configuración guardada!", True, (100, 255, 100))
        save_msg_rect = save_msg.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, SAVE_BUTTON_Y + 60)
        )
        screen.blit(save_msg, save_msg_rect)

    def _render_instructions(self, screen):
        instructions = self.label_font.render(
            "Flechas: Navegar | Izq/Der: Volumen | Enter: Guardar | ESC: Volver", True, (150, 150, 150)
        )
        instructions_rect = instructions.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT - 30)
        )
        screen.blit(instructions, instructions_rect)
