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
VOLUME_SLIDER_Y = 200
SLIDER_LABEL_OFFSET = 40
SAVE_BUTTON_Y = 400

class VolumeSlider:

    def __init__(self, x, y, initial_value=0.5):
        self.x = x
        self.y = y
        self.width = SLIDER_WIDTH
        self.height = SLIDER_HEIGHT
        self.value = initial_value
        self.dragging = False

        self.bg_rect = pygame.Rect(x, y, self.width, self.height)
        self.handle_x = self._value_to_x(self.value)

    def _value_to_x(self, value):
        return self.x + int(value * self.width)

    def _x_to_value(self, x):
        relative_x = max(0, min(x - self.x, self.width))
        raw_value = relative_x / self.width
        # Snap to 10% increments
        snapped_value = round(raw_value * 10) / 10
        return snapped_value

    def handle_event(self, event):
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
        return self.value

    def set_value(self, value):
        self.value = max(VOLUME_MIN, min(value, VOLUME_MAX))
        self.handle_x = self._value_to_x(self.value)

    def render(self, screen):
        pygame.draw.rect(screen, SLIDER_BG_COLOR, self.bg_rect, border_radius=5)

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
            text="Save Settings",
        )
        # Center the button
        self.base_rect.centerx = ScreenSettings.SCREEN_WIDTH // 2

    def action(self):
        self.screen.save_settings()

class SettingsScene(PyGameScene):

    def __init__(self, director):
        super().__init__(director)
        pygame.font.init()
        self.title_font = pygame.font.SysFont(GUISettings.FONT_TEXT, TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont(GUISettings.FONT_TEXT, LABEL_FONT_SIZE)
        saved_volume = SettingsManager.get_volume()
        slider_x = ScreenSettings.SCREEN_WIDTH // 2 - 150
        self.volume_slider = VolumeSlider(slider_x, VOLUME_SLIDER_Y, saved_volume)
        self.save_button = SaveButton(self)
        self.volume_controller = VolumeController()
        self.volume_controller.set_volume(self.volume_slider.get_value())

        self.show_save_message = False
        self.save_message_timer = 0

    def update(self, delta_time):
        # Update volume in real-time as slider changes
        self.volume_controller.set_volume(self.volume_slider.get_value())
        if self.show_save_message:
            self.save_message_timer += delta_time
            if self.save_message_timer >= 2000:
                self.show_save_message = False
                self.save_message_timer = 0

    def events(self, event_list):
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.director.exitScene()
            self.volume_slider.handle_event(event)
            if event.type == MOUSEBUTTONDOWN:
                if self.save_button.base_rect.collidepoint(event.pos):
                    self.save_button.click_element = self.save_button
            elif event.type == MOUSEBUTTONUP:
                if self.save_button.base_rect.collidepoint(event.pos):
                    if hasattr(self.save_button, 'click_element') and self.save_button.click_element == self.save_button:
                        self.save_button.action()
                self.save_button.click_element = None

    def render(self, screen):
        screen.fill(BACKGROUND_COLOR)
        self._render_title(screen)
        self._render_volume_section(screen)
        self.save_button.render(screen)
        if self.show_save_message:
            self._render_save_confirmation(screen)
        self._render_instructions(screen)

    def _render_title(self, screen):
        title_text = self.title_font.render("Settings", True, TEXT_COLOR)
        title_rect = title_text.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, TITLE_Y)
        )
        screen.blit(title_text, title_rect)

    def _render_volume_section(self, screen):
        # Volume label
        volume_label = self.label_font.render("Volume", True, TEXT_COLOR)
        label_rect = volume_label.get_rect(
            center=(
                ScreenSettings.SCREEN_WIDTH // 2,
                VOLUME_SLIDER_Y - SLIDER_LABEL_OFFSET,
            )
        )
        screen.blit(volume_label, label_rect)
        self.volume_slider.render(screen)

        volume_percent = int(self.volume_slider.get_value() * 100)
        percent_text = self.label_font.render(f"{volume_percent}%", True, TEXT_COLOR)
        percent_rect = percent_text.get_rect(
            center=(
                ScreenSettings.SCREEN_WIDTH // 2,
                VOLUME_SLIDER_Y + SLIDER_LABEL_OFFSET,
            )
        )
        screen.blit(percent_text, percent_rect)

    def _render_save_confirmation(self, screen):
        save_msg = self.label_font.render("Settings saved!", True, (100, 255, 100))
        save_msg_rect = save_msg.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, SAVE_BUTTON_Y + 60)
        )
        screen.blit(save_msg, save_msg_rect)

    def _render_instructions(self, screen):
        instructions = self.label_font.render(
            "Press ESC to return", True, (150, 150, 150)
        )
        instructions_rect = instructions.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT - 50)
        )
        screen.blit(instructions, instructions_rect)

    def save_settings(self):
        settings = {"volume": self.volume_slider.get_value()}
        if SettingsManager.save_settings(settings):
            self.show_save_message = True
            self.save_message_timer = 0
