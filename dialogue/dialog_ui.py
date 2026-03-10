import pygame

class DialogueUI:
    def __init__(self, name, full_text, portrait, side, font):
        self.name = name
        self.full_text = full_text
        self.portrait = portrait
        self.side = side 
        self.font = font
        
        self.anim_progress = 0.0 
        self.anim_speed = 7.0
        self.entry_mode = "pop" 
        self.animations = {"slide": self._anim_slide, "pop": self._anim_pop}
        
        self.box_width = 620 
        self.bg_color = (255, 255, 255)
        self.border_color = (40, 40, 40)
        self.text_color = (20, 20, 20)
        self.name_color = (200, 50, 50) if side == "left" else (50, 50, 200)
        self.border_width = 2
        self.padding_x = 25
        self.padding_y = 20
        self._is_intro_anim = False 

    def _anim_slide(self, rect, progress):
        offset = (-15 if self._is_intro_anim else 15) * (1.0 - progress)
        rect.y += offset
        return rect

    def _anim_pop(self, rect, progress):
        new_w, new_h = rect.width * progress, rect.height * progress
        new_rect = pygame.Rect(0, 0, new_w, new_h); new_rect.center = rect.center
        return new_rect

    def update_anim(self, dt):
        if self.anim_progress < 1.0:
            self.anim_progress += self.anim_speed * dt
            if self.anim_progress > 1.0: self.anim_progress = 1.0

    def draw(self, screen, y_pos, current_text, fixed_x, is_last=False, is_intro=False):
        self._is_intro_anim = is_intro
        screen_w = screen.get_width()
        start_x = fixed_x if self.side == 'left' else screen_w - self.box_width - fixed_x
        final_h = self.get_expected_height()
        target_rect = pygame.Rect(start_x, y_pos, self.box_width, final_h)

        anim_func = self.animations.get(self.entry_mode, self._anim_slide)
        draw_rect = anim_func(target_rect.copy(), self.anim_progress)

        if self.anim_progress > 0.1:
            shadow_rect = draw_rect.copy(); shadow_rect.move_ip(4, 4)
            pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=8)
            pygame.draw.rect(screen, self.bg_color, draw_rect, border_radius=8)
            pygame.draw.rect(screen, self.border_color, draw_rect, width=self.border_width, border_radius=8)

            if self.name and self.anim_progress > 0.5:
                name_font = pygame.font.SysFont("arial", 15, bold=True)
                name_surf = name_font.render(self.name.upper(), True, self.name_color)
                name_rect = name_surf.get_rect()
                if self.side == 'left': name_rect.topleft = (draw_rect.x + 15, draw_rect.y - 12)
                else: name_rect.topright = (draw_rect.right - 15, draw_rect.y - 12)
                bg_name = name_rect.inflate(10, 4)
                pygame.draw.rect(screen, self.bg_color, bg_name, border_radius=3)
                pygame.draw.rect(screen, self.border_color, bg_name, width=1, border_radius=3)
                screen.blit(name_surf, name_rect)

            if self.anim_progress > 0.8:
                self._draw_content(screen, draw_rect, current_text, is_last)

        return final_h

    def _draw_content(self, screen, rect, current_text, is_last=False):
        draw_y = rect.y; text_margin = 0
        if self.portrait:
            p_img = pygame.transform.smoothscale(self.portrait, (80, 80)); text_margin = 95
            if self.side == 'right':
                p_x = rect.right - 80 - self.padding_x; text_x = rect.x + self.padding_x
            else:
                p_x = rect.x + self.padding_x; text_x = p_x + text_margin
            p_rect = pygame.Rect(p_x, draw_y + (rect.height - 80) // 2, 80, 80)
            pygame.draw.ellipse(screen, (230, 230, 230), p_rect); screen.blit(p_img, p_rect.topleft)
        else: text_x = rect.x + self.padding_x

        wrap_width = self.box_width - text_margin - (self.padding_x * 2)
        current_lines = self._wrap_text(current_text, wrap_width)
        line_height = self.font.get_height() + 4
        total_text_h = len(self._wrap_text(self.full_text, wrap_width)) * line_height
        text_block_y = draw_y + (rect.height - total_text_h) // 2
        
        for i, line in enumerate(current_lines):
            t_surf = self.font.render(line, True, self.text_color)
            screen.blit(t_surf, (text_x, text_block_y + i * line_height))

        if is_last and current_text.strip() == self.full_text.strip():
            time_blink = pygame.time.get_ticks() % 1000
            if time_blink > 400:
                small_font = pygame.font.SysFont("sans-serif", 14, bold=True)
                hint_surf = small_font.render("▼ ESPACIO", True, (120, 120, 120))
                screen.blit(hint_surf, (rect.right - hint_surf.get_width() - 15, rect.bottom - hint_surf.get_height() - 8))

    def _wrap_text(self, text, max_w):
        if not text: return []
        words = text.split(' '); lines = []; curr = ""
        for w in words:
            if self.font.size((curr + " " + w).strip())[0] <= max_w: curr = (curr + " " + w).strip()
            else:
                if curr: lines.append(curr)
                curr = w
        if curr: lines.append(curr)
        return lines

    def get_expected_height(self):
        text_margin = 95 if self.portrait else 0
        wrap_width = self.box_width - text_margin - (self.padding_x * 2)
        full_lines = self._wrap_text(self.full_text, wrap_width)
        line_height = self.font.get_height() + 4
        content_h = (len(full_lines) * line_height) + (self.padding_y * 2)
        return max(content_h, 85)