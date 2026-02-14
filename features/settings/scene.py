from features.common.scene import PyGameScene
from features.settings.ui.slider import VolumeSlider
from features.settings.ui.buttons import SaveButton
from features.settings.lib.storage import SettingsManager
from features.settings.lib.volume import VolumeController
from features.settings.constants import (
    BACKGROUND_COLOR,
    TITLE_Y,
    VOLUME_SLIDER_Y,
    SLIDER_LABEL_OFFSET,
    SAVE_BUTTON_Y,
    TITLE_FONT_SIZE,
    LABEL_FONT_SIZE,
    TEXT_COLOR,
)
from settings import ScreenSettings, GUISettings
import pygame
from pygame.locals import *


class SettingsScene(PyGameScene):
    """
    Settings screen scene
    Allows users to configure game settings like volume
    """

    def __init__(self, director):
        super().__init__(director)

        # Initialize fonts
        pygame.font.init()
        self.title_font = pygame.font.SysFont(
            GUISettings.FONT_TEXT, TITLE_FONT_SIZE, bold=True
        )
        self.label_font = pygame.font.SysFont(GUISettings.FONT_TEXT, LABEL_FONT_SIZE)

        # Load saved volume or use default
        saved_volume = SettingsManager.get_volume()

        # Create volume slider centered horizontally
        slider_x = (
            ScreenSettings.SCREEN_WIDTH // 2 - 150
        )  # Center the 300px wide slider
        self.volume_slider = VolumeSlider(slider_x, VOLUME_SLIDER_Y, saved_volume)

        # Create save button
        self.save_button = SaveButton(self)

        # Set initial volume
        VolumeController.set_volume(self.volume_slider.get_value())

        # Save confirmation message state
        self.show_save_message = False
        self.save_message_timer = 0

    def update(self, delta_time):
        """Update scene state"""
        # Update volume in real-time as slider changes
        VolumeController.set_volume(self.volume_slider.get_value())

        # Update save message timer
        if self.show_save_message:
            self.save_message_timer += delta_time
            if self.save_message_timer >= 2000:  # Show for 2 seconds
                self.show_save_message = False
                self.save_message_timer = 0

    def events(self, event_list):
        """Handle input events"""
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.director.exitScene()

            # Pass events to volume slider
            self.volume_slider.handle_event(event)

            # Handle button clicks
            if event.type == MOUSEBUTTONDOWN:
                if self.save_button.base_rect.collidepoint(event.pos):
                    self.save_button.click_element = self.save_button
            elif event.type == MOUSEBUTTONUP:
                if self.save_button.base_rect.collidepoint(event.pos):
                    if self.save_button.click_element == self.save_button:
                        self.save_button.action()
                self.save_button.click_element = None

    def render(self, screen):
        """Render the settings screen"""
        screen.fill(BACKGROUND_COLOR)

        # Render title
        self._render_title(screen)

        # Render volume controls
        self._render_volume_section(screen)

        # Render save button
        self.save_button.render(screen)

        # Render save confirmation if active
        if self.show_save_message:
            self._render_save_confirmation(screen)

        # Render footer instructions
        self._render_instructions(screen)

    def _render_title(self, screen):
        """Render the settings title"""
        title_text = self.title_font.render("Settings", True, TEXT_COLOR)
        title_rect = title_text.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, TITLE_Y)
        )
        screen.blit(title_text, title_rect)

    def _render_volume_section(self, screen):
        """Render volume label, slider, and percentage"""
        # Volume label
        volume_label = self.label_font.render("Volume", True, TEXT_COLOR)
        label_rect = volume_label.get_rect(
            center=(
                ScreenSettings.SCREEN_WIDTH // 2,
                VOLUME_SLIDER_Y - SLIDER_LABEL_OFFSET,
            )
        )
        screen.blit(volume_label, label_rect)

        # Volume slider
        self.volume_slider.render(screen)

        # Volume percentage
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
        """Render save success message"""
        save_msg = self.label_font.render("Settings saved!", True, (100, 255, 100))
        save_msg_rect = save_msg.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, SAVE_BUTTON_Y + 60)
        )
        screen.blit(save_msg, save_msg_rect)

    def _render_instructions(self, screen):
        """Render footer instructions"""
        instructions = self.label_font.render(
            "Press ESC to return", True, (150, 150, 150)
        )
        instructions_rect = instructions.get_rect(
            center=(ScreenSettings.SCREEN_WIDTH // 2, ScreenSettings.SCREEN_HEIGHT - 50)
        )
        screen.blit(instructions, instructions_rect)

    def save_settings(self):
        """Save current settings to file"""
        settings = {"volume": self.volume_slider.get_value()}
        if SettingsManager.save_settings(settings):
            self.show_save_message = True
            self.save_message_timer = 0
