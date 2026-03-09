import pygame
import random
import Box2D
import math
from match_scene import MatchScene, px2m, m2px, SW, SH, PPM
from settings import ScreenSettings
from factory import RocketFactory

# ─── CONSTANTES DEL ESCENARIO 2 ──────────────────────────────

GROUND_Y   = 570
GOAL_W     = 100
GOAL_H     = 160
GOAL_POST  = 6
GOAL_TOP_Y = GROUND_Y - GOAL_H + 30

BG_COLOR       = (40, 40, 80)
GROUND_COLOR   = (30, 30, 60)
GOAL_COLOR     = (255, 255, 255)
GOAL_NET_COLOR = (180, 180, 180, 80)

# Boss MotoMoto
BOSS_START = (SW - 200, GROUND_Y - 40)

# Indicadores
ANGRY_INDICATOR_COLOR = (255, 80, 30)
ANGRY_INDICATOR_POS   = (SW - 10, 10)

# Teletransporte visual
TELEPORT_FLASH_DURATION = 500
TELEPORT_COLOR          = (0, 255, 255)

# ─── NUBES (obstáculos con rebote) ───────────────────────────

CLOUD_SPAWN_INTERVAL  = 6000
CLOUD_LIFETIME        = 12000
CLOUD_MAX_ACTIVE      = 5
CLOUD_MIN_W           = 70
CLOUD_MAX_W           = 140
CLOUD_H               = 30
CLOUD_MARGIN_X        = 100
CLOUD_MIN_Y           = GOAL_TOP_Y
CLOUD_MAX_Y           = GROUND_Y - CLOUD_H
CLOUD_RESTITUTION     = 3.0
CLOUD_FRICTION        = 0.0
CLOUD_COLOR           = (0, 0, 0)
CLOUD_BORDER_COLOR    = (40, 40, 40)
CLOUD_FADE_TIME       = 1500
CLOUD_BOUNCE_IMPULSE  = 25.0

# ─── POWER-UP: PELOTAZO ──────────────────────────────────────

POWERUP_KICK_RANGE     = 5.0
POWERUP_KICK_SPEED     = 1000.0
POWERUP_KICK_COLOR     = (255, 100, 0)
POWERUP_FLASH_DURATION = 400
POWERUP_READY_COLOR    = (0, 255, 200)


# ─── CONTACT LISTENER ────────────────────────────────────────

class Scene2ContactListener(Box2D.b2ContactListener):
    """
    Listener Box2D para el escenario 2.
    Detecta colisiones con nubes y encola impulsos de rebote extra
    que se aplican DESPUÉS del world.Step.
    """

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self._pending_bounces = []

    def _get_cloud_contact(self, contact):
        fA = contact.fixtureA
        fB = contact.fixtureB
        udA = fA.userData
        udB = fB.userData

        cloud_is_A = isinstance(udA, dict) and udA.get('type') == 'cloud'
        cloud_is_B = isinstance(udB, dict) and udB.get('type') == 'cloud'

        if not (cloud_is_A or cloud_is_B):
            return None

        dynamic_body = fB.body if cloud_is_A else fA.body
        if dynamic_body.type != Box2D.b2_dynamicBody:
            return None

        try:
            nx, ny = contact.worldManifold.normal
        except Exception:
            nx, ny = 0.0, -1.0

        if cloud_is_B:
            nx, ny = -nx, -ny

        return (dynamic_body, nx, ny)

    def BeginContact(self, contact):
        result = self._get_cloud_contact(contact)
        if result:
            body, nx, ny = result
            self._pending_bounces.append((body, nx, ny))

    def EndContact(self, contact):
        pass

    def apply_pending_bounces(self):
        for body, nx, ny in self._pending_bounces:
            try:
                ix = nx * CLOUD_BOUNCE_IMPULSE
                iy = ny * CLOUD_BOUNCE_IMPULSE

                if abs(ny) < 0.3:
                    iy = -abs(CLOUD_BOUNCE_IMPULSE) * 0.6

                body.ApplyLinearImpulse(
                    impulse=(ix, iy),
                    point=body.worldCenter,
                    wake=True
                )
            except Exception:
                pass
        self._pending_bounces.clear()


# ─── SECOND SCENE ────────────────────────────────────────────

class SecondScene(MatchScene):
    """Escenario 2: MotoMoto + nubes negras rebotadoras + power-up pelotazo."""

    def _get_config(self):
        return {
            'ground_y':      GROUND_Y,
            'player_start':  (200, GROUND_Y - 60),
            'ball_start':    (SW // 2, GROUND_Y - 220),
            'gravity':       (0, 35),
            'player_speed':  12.0,
            'player_jump':   -28.0,
            'ground_blend':  0.35,
            'air_blend':     0.12,
            'player_hh':     3.5,
            'goal_pause_ms': 2000,
        }

    # ─── INIT EXTRAS ─────────────────────────────────────────

    def _init_extras(self):
        """Crea a MotoMoto, el contact listener, las nubes y el sistema de pelotazo."""
        self.contact_listener = Scene2ContactListener(self)
        self.world.contactListener = self.contact_listener

        # Boss
        self.boss = RocketFactory.create_element(
            "boss", self.world, BOSS_START, subtipo='motomoto'
        )
        self.grupo_sprites.add(self.boss)

        # Fuentes para indicadores
        self.angry_font = pygame.font.SysFont('Arial', 18, bold=True)
        self.kick_font  = pygame.font.SysFont('Arial', 22, bold=True)

        # ─── Teletransporte ───────────────────────────────────
        self.teleport_flash_timer = 0
        self.teleport_flash_pos   = None

        # Control: solo 1 TP por episodio de enfado
        self._teleport_used_this_anger = False
        self._boss_was_angry           = False

        # ─── Nubes ────────────────────────────────────────────
        self.clouds            = []
        self.cloud_spawn_timer = CLOUD_SPAWN_INTERVAL * 0.3

        # ─── Pelotazo (power-up) ──────────────────────────────
        self.kick_flash_timer = 0
        self.kick_flash_pos   = None

    # ─── NUBES: OBSTÁCULOS BOX2D (delegado a RocketFactory) ──

    def _spawn_cloud(self):
        """Crea una nube negra como cuerpo estático Box2D con alto rebote."""
        if len(self.clouds) >= CLOUD_MAX_ACTIVE:
            return

        w_px = random.randint(CLOUD_MIN_W, CLOUD_MAX_W)
        x_px = random.randint(CLOUD_MARGIN_X, SW - CLOUD_MARGIN_X - w_px)
        y_px = random.randint(CLOUD_MIN_Y, CLOUD_MAX_Y)

        # Evitar solapamiento con nubes existentes
        new_rect = pygame.Rect(x_px, y_px, w_px, CLOUD_H)
        for c in self.clouds:
            if new_rect.colliderect(c['rect'].inflate(20, 20)):
                return

        body = RocketFactory.create_cloud(
            self.world, x_px, y_px, w_px, CLOUD_H,
            friction=CLOUD_FRICTION, restitution=CLOUD_RESTITUTION
        )

        self.clouds.append({'rect': new_rect, 'body': body, 'timer': 0})

    def _destroy_cloud_body(self, body):
        """Elimina un cuerpo de nube del mundo Box2D."""
        RocketFactory.destroy_body(self.world, body)

    def _update_clouds(self, delta_time):
        """Spawn, envejecimiento y eliminación de nubes."""
        self.cloud_spawn_timer += delta_time
        if self.cloud_spawn_timer >= CLOUD_SPAWN_INTERVAL:
            self.cloud_spawn_timer = 0
            self._spawn_cloud()

        for cloud in self.clouds:
            cloud['timer'] += delta_time

        alive = []
        for c in self.clouds:
            if c['timer'] < CLOUD_LIFETIME:
                alive.append(c)
            else:
                self._destroy_cloud_body(c['body'])
        self.clouds = alive

    # ─── POWER-UP: PELOTAZO ──────────────────────────────────

    def _on_powerup_collected(self):
        """Se llama cuando el jugador recoge la caja de power-up."""
        pass

    def _on_powerup_activate(self):
        """El jugador pulsa E para lanzar un pelotazo si está cerca del balón."""
        if not self.player_has_powerup:
            return
        if not self.jugador.body or not self.pelota.body:
            return

        player_pos = self.jugador.body.position
        ball_pos   = self.pelota.body.position

        dx   = ball_pos.x - player_pos.x
        dy   = ball_pos.y - player_pos.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > POWERUP_KICK_RANGE:
            return

        if dist < 0.01:
            dir_x, dir_y = 1.0, -0.3
        else:
            dir_x = dx / dist
            dir_y = dy / dist

        self.pelota.body.linearVelocity = (0, 0)
        self.pelota.body.ApplyLinearImpulse(
            impulse=(dir_x * POWERUP_KICK_SPEED, dir_y * POWERUP_KICK_SPEED),
            point=self.pelota.body.worldCenter,
            wake=True
        )

        self.player_has_powerup = False

        self.kick_flash_timer = POWERUP_FLASH_DURATION
        self.kick_flash_pos   = (int(m2px(ball_pos.x)), int(m2px(ball_pos.y)))

    # ─── BOUNDARIES & GOALS (delegado a RocketFactory) ───────

    def _create_boundaries(self):
        RocketFactory.create_boundaries(self.world, SW, GROUND_Y, GOAL_TOP_Y)

    def _create_goals(self):
        return RocketFactory.create_goals(
            self.world, SW, GROUND_Y, GOAL_W, GOAL_H, GOAL_POST, GOAL_TOP_Y
        )

    # ─── IA DEL BOSS ─────────────────────────────────────────

    def _update_boss_ai(self, delta_time):
        """Actualiza la IA de MotoMoto: reloj interno + 1 TP por enfado + FSM."""
        if not (hasattr(self, 'boss') and self.boss.body
                and self.pelota.body and self.jugador.body):
            return

        if hasattr(self.boss, 'update_logic'):
            self.boss.update_logic(delta_time)

        currently_angry = self.boss.is_angry
        if self._boss_was_angry and not currently_angry:
            self._teleport_used_this_anger = False
        self._boss_was_angry = currently_angry

        if currently_angry and not self._teleport_used_this_anger:
            goal_x_right_m = px2m(SW - GOAL_W / 2)
            goal_y_m       = px2m(GROUND_Y - 40)

            if hasattr(self.boss, 'try_teleport_to_goal'):
                teleported = self.boss.try_teleport_to_goal(
                    self.pelota.body.position,
                    goal_x_right_m,
                    goal_y_m
                )
                if teleported:
                    self._teleport_used_this_anger = True
                    self.teleport_flash_timer = TELEPORT_FLASH_DURATION
                    self.teleport_flash_pos   = (
                        int(m2px(self.boss.body.position.x)),
                        int(m2px(self.boss.body.position.y))
                    )

        self.boss.update_fsm(
            ball_pos=self.pelota.body.position,
            player_pos=self.jugador.body.position,
            goal_x_right=SW / PPM
        )

    # ─── RESET ────────────────────────────────────────────────

    def _reset_positions(self):
        super()._reset_positions()

        if hasattr(self, 'boss') and self.boss.body:
            self.boss.body.position        = (px2m(BOSS_START[0]), px2m(BOSS_START[1]))
            self.boss.body.linearVelocity  = (0, 0)
            self.boss.body.angularVelocity = 0


        if not (hasattr(self, 'boss') and self.boss.is_angry):
            self._teleport_used_this_anger = False

        self._boss_was_angry = self.boss.is_angry if hasattr(self, 'boss') else False

        self.teleport_flash_timer = 0
        self.teleport_flash_pos   = None
        self.kick_flash_timer     = 0
        self.kick_flash_pos       = None

    # ─── UPDATE ───────────────────────────────────────────────

    def update(self, delta_time):
        super().update(delta_time)

        if hasattr(self, 'contact_listener'):
            self.contact_listener.apply_pending_bounces()

        self._update_boss_ai(delta_time)
        self._update_clouds(delta_time)

        if self.teleport_flash_timer > 0:
            self.teleport_flash_timer = max(0, self.teleport_flash_timer - delta_time)

        if self.kick_flash_timer > 0:
            self.kick_flash_timer = max(0, self.kick_flash_timer - delta_time)

    # ─── RENDER ───────────────────────────────────────────────

    def _render_field(self, screen):
        if not hasattr(self, '_stadium_bg'):
            try:
                bg = pygame.image.load('./assets/stadiums/stadium2_bg.png').convert()
                self._stadium_bg = pygame.transform.scale(bg, (SW, SH))
            except Exception:
                self._stadium_bg = pygame.Surface((SW, SH))
                self._stadium_bg.fill(BG_COLOR)
        screen.blit(self._stadium_bg, (0, 0))

        if not hasattr(self, '_goalpost_bg'):
            try:
                l_yellow_container_bg    = pygame.image.load('./assets/stadiums/contenedor_left_yellow_bg.png').convert_alpha()
                r_green_container_bg    = pygame.image.load('./assets/stadiums/contenedor_right_green_bg.png').convert_alpha()

                l_yellow_container_bg_scaled = pygame.transform.scale(l_yellow_container_bg, (GOAL_W*2, GOAL_H))
                r_green_container_bg_scaled = pygame.transform.scale(r_green_container_bg, (GOAL_W*2, GOAL_H))
                
                self._goalpost_bg_l = l_yellow_container_bg_scaled
                self._goalpost_bg_r = r_green_container_bg_scaled
            except Exception:
                self._goalpost_bg_l = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
                pygame.draw.rect(self._goalpost_bg_l, (*GOAL_NET_COLOR,), (0, 0, GOAL_W, GOAL_H))
                self._goalpost_bg_r = self._goalpost_bg_l.copy()
            self._goalpost_bg = True

        screen.blit(self._goalpost_bg_l, (0, GOAL_TOP_Y))
        screen.blit(self._goalpost_bg_r, (SW - GOAL_W*2, GOAL_TOP_Y))

        self._draw_clouds(screen)

    def _render_field_fg(self, screen):
        if not hasattr(self, '_goalpost_fg'):
            try:
                l_yellow_container_fg    = pygame.image.load('./assets/stadiums/contenedor_left_yellow_fg.png').convert_alpha()
                r_green_container_fg    = pygame.image.load('./assets/stadiums/contenedor_right_green_fg.png').convert_alpha()

                l_yellow_container_fg_scaled = pygame.transform.scale(l_yellow_container_fg, (GOAL_W*2, GOAL_H))
                r_green_container_fg_scaled = pygame.transform.scale(r_green_container_fg , (GOAL_W*2, GOAL_H))

                self._goalpost_fg_l = l_yellow_container_fg_scaled
                self._goalpost_fg_r = r_green_container_fg_scaled
            except Exception:
                self._goalpost_fg_l = pygame.Surface((GOAL_W*2, GOAL_H), pygame.SRCALPHA)
                self._goalpost_fg_r = self._goalpost_fg_l.copy()
            self._goalpost_fg = True

        screen.blit(self._goalpost_fg_l, (0, GOAL_TOP_Y))
        screen.blit(self._goalpost_fg_r, (SW - GOAL_W*2, GOAL_TOP_Y))

    def render(self, screen):
        super().render(screen)
        self._draw_angry_indicator(screen)
        self._draw_teleport_flash(screen)
        self._draw_kick_flash(screen)
        self._draw_kick_hud(screen)

    # ─── DIBUJO DE NUBES ─────────────────────────────────────

    def _draw_clouds(self, screen):
        """Dibuja las nubes negras con fade-in y fade-out."""
        for cloud in self.clouds:
            rect  = cloud['rect']
            timer = cloud['timer']

            if timer < CLOUD_FADE_TIME:
                alpha = int(220 * (timer / CLOUD_FADE_TIME))
            elif timer > CLOUD_LIFETIME - CLOUD_FADE_TIME:
                alpha = int(220 * ((CLOUD_LIFETIME - timer) / CLOUD_FADE_TIME))
            else:
                alpha = 220
            alpha = max(0, min(220, alpha))

            cloud_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

            pygame.draw.rect(cloud_surf, (*CLOUD_COLOR, alpha),
                             (0, 0, rect.width, rect.height), border_radius=16)

            pygame.draw.rect(cloud_surf, (*CLOUD_BORDER_COLOR, min(alpha + 40, 255)),
                             (0, 0, rect.width, rect.height), 2, border_radius=16)

            bulge_alpha = max(0, alpha - 20)
            num_bulges  = max(2, rect.width // 30)
            for i in range(num_bulges):
                bx = 15 + i * (rect.width - 30) // max(1, num_bulges - 1)
                by = rect.height // 2 - 5
                pygame.draw.circle(cloud_surf, (*CLOUD_COLOR, bulge_alpha), (bx, by), 15)

            if alpha > 100:
                warn_font = pygame.font.SysFont('Arial', 14, bold=True)
                warn_text = warn_font.render("⚡", True, (255, 255, 255, alpha))
                cloud_surf.blit(warn_text, warn_text.get_rect(
                    center=(rect.width // 2, rect.height // 2)))

            screen.blit(cloud_surf, (rect.x, rect.y))

    # ─── INDICADORES VISUALES ─────────────────────────────────

    def _draw_angry_indicator(self, screen):
        if not hasattr(self, 'boss'):
            return

        if self.boss.is_angry:
            blink = (pygame.time.get_ticks() // 400) % 2 == 0
            color = ANGRY_INDICATOR_COLOR if blink else (200, 60, 30)
            tp_tag = " [TP USADO]" if self._teleport_used_this_anger else " [TP LISTO]"
            label  = "⚠ MOTOMOTO ENFADADO!" + tp_tag
            text   = self.angry_font.render(label, True, color)
        else:
            remaining_s = max(0, (30000 - self.boss.angry_timer) / 1000)
            label = f"MotoMoto: calmado  ({remaining_s:.0f}s)"
            text  = self.angry_font.render(label, True, (150, 255, 150))

        rect = text.get_rect(topright=ANGRY_INDICATOR_POS)
        bg   = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        screen.blit(bg, (rect.x - 8, rect.y - 4))
        screen.blit(text, rect)

    def _draw_teleport_flash(self, screen):
        if self.teleport_flash_timer <= 0 or self.teleport_flash_pos is None:
            return

        ratio  = self.teleport_flash_timer / TELEPORT_FLASH_DURATION
        alpha  = max(0, min(255, int(255 * ratio)))
        cx, cy = self.teleport_flash_pos
        radius = int(40 * ratio) + 10

        flash_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(flash_surf, (*TELEPORT_COLOR, alpha // 2), (radius, radius), radius)
        pygame.draw.circle(flash_surf, (*TELEPORT_COLOR, alpha),      (radius, radius), max(4, radius // 2))
        screen.blit(flash_surf, (cx - radius, cy - radius))

        t = pygame.time.get_ticks() / 150.0
        for i in range(6):
            angle = t + i * (2 * math.pi / 6)
            d  = radius * 0.8
            px = cx + int(d * math.cos(angle))
            py = cy + int(d * math.sin(angle))
            pygame.draw.circle(screen, TELEPORT_COLOR, (px, py), 3)

    def _draw_kick_flash(self, screen):
        if self.kick_flash_timer <= 0 or self.kick_flash_pos is None:
            return

        ratio  = self.kick_flash_timer / POWERUP_FLASH_DURATION
        alpha  = max(0, min(255, int(255 * ratio)))
        cx, cy = self.kick_flash_pos
        radius = int(50 * ratio) + 8

        flash_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(flash_surf, (*POWERUP_KICK_COLOR, alpha // 3),
                           (radius, radius), radius)
        pygame.draw.circle(flash_surf, (*POWERUP_KICK_COLOR, alpha),
                           (radius, radius), max(4, radius // 3))
        screen.blit(flash_surf, (cx - radius, cy - radius))

        if ratio > 0.5:
            kick_text = self.kick_font.render("💥 KICK!", True, POWERUP_KICK_COLOR)
            screen.blit(kick_text, kick_text.get_rect(center=(cx, cy - 30)))

        t = pygame.time.get_ticks() / 100.0
        for i in range(8):
            angle      = t + i * (2 * math.pi / 8)
            inner_dist = radius * 0.4
            outer_dist = radius * 0.9
            x1 = cx + int(inner_dist * math.cos(angle))
            y1 = cy + int(inner_dist * math.sin(angle))
            x2 = cx + int(outer_dist * math.cos(angle))
            y2 = cy + int(outer_dist * math.sin(angle))
            pygame.draw.line(screen, (*POWERUP_KICK_COLOR, alpha), (x1, y1), (x2, y2), 2)

    def _draw_kick_hud(self, screen):
        if not self.player_has_powerup:
            return

        if self.jugador.body and self.pelota.body:
            player_pos = self.jugador.body.position
            ball_pos   = self.pelota.body.position
            dx   = ball_pos.x - player_pos.x
            dy   = ball_pos.y - player_pos.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= POWERUP_KICK_RANGE:
                color = (0, 255, 100)
                label = "⚡ PELOTAZO LISTO [E] - ¡EN RANGO!"
            else:
                color = (255, 200, 0)
                label = f"⚡ PELOTAZO [E] - Acércate ({dist:.1f}m)"

            text = self.kick_font.render(label, True, color)
            rect = text.get_rect(bottomleft=(10, SH - 40))
            bg   = pygame.Surface((rect.width + 12, rect.height + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            screen.blit(bg, (rect.x - 6, rect.y - 4))
            screen.blit(text, rect)