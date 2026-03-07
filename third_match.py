import pygame
import random
import Box2D
import math
from match_scene import MatchScene, px2m, m2px, SW, SH, PPM
from settings import ScreenSettings
from factory import RocketFactory

# ─── CONSTANTES DEL ESCENARIO 3 ──────────────────────────────

GROUND_Y   = 570
GOAL_W     = 150
GOAL_H     = 320
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

CLOUD_SPAWN_INTERVAL  = 6000              # ms entre spawns de nubes
CLOUD_LIFETIME        = 12000             # ms que dura una nube
CLOUD_MAX_ACTIVE      = 5
CLOUD_MIN_W           = 70               # px ancho mínimo
CLOUD_MAX_W           = 140              # px ancho máximo
CLOUD_H               = 30              # px alto
CLOUD_MARGIN_X        = 100              # px margen lateral
CLOUD_MIN_Y           = int(SH * 0.05)  # 5% desde arriba
CLOUD_MAX_Y           = int(SH * 0.75)  # hasta 3/4 de pantalla (evita el suelo)
CLOUD_RESTITUTION     = 3.0             # rebote alto en la fixture Box2D
CLOUD_FRICTION        = 0.0
CLOUD_COLOR           = (0, 0, 0)        # negro
CLOUD_BORDER_COLOR    = (40, 40, 40)     # negro ligeramente más claro para el borde
CLOUD_FADE_TIME       = 1500             # ms de fade-in/fade-out
CLOUD_BOUNCE_IMPULSE  = 25.0            # impulso extra aplicado al colisionar

# ─── POWER-UP: PELOTAZO ──────────────────────────────────────

POWERUP_KICK_RANGE     = 5.0            # metros de distancia al balón para activar
POWERUP_KICK_SPEED     = 1000.0         # m/s velocidad del pelotazo
POWERUP_KICK_COLOR     = (255, 100, 0)
POWERUP_FLASH_DURATION = 400            # ms del efecto visual del pelotazo
POWERUP_READY_COLOR    = (0, 255, 200)


# ─── CONTACT LISTENER ────────────────────────────────────────

class Scene2ContactListener(Box2D.b2ContactListener):
    """
    Listener Box2D para el escenario 2.
    Detecta colisiones con nubes y encola impulsos de rebote extra
    que se aplican DESPUÉS del world.Step (nunca dentro del callback).
    """

    def __init__(self, scene):
        super().__init__()
        self.scene = scene

# ─── SECOND SCENE ────────────────────────────────────────────

class ThirdMatch(MatchScene):
    """Escenario 3: La Jenny"""

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
        """Crea a La Jenny, el contact listener, las nubes y el sistema de pelotazo."""
        # Contact listener con detección de nubes
        self.contact_listener = Scene2ContactListener(self)
        self.world.contactListener = self.contact_listener

        # Boss
        self.boss = RocketFactory.create_element(
            "boss", self.world, BOSS_START, subtipo='lajenny'
        )
        self.grupo_sprites.add(self.boss)

        # Fuentes para indicadores
        self.angry_font = pygame.font.SysFont('Arial', 18, bold=True)

        # ─── Teletransporte ───────────────────────────────────
        self.teleport_flash_timer = 0
        self.teleport_flash_pos   = None

        # Control: solo 1 TP por episodio de enfado
        self._teleport_used_this_anger = False
        self._boss_was_angry           = False

    # ─── POWER-UP: PELOTAZO ──────────────────────────────────

    def _on_powerup_collected(self):
        """Se llama cuando el jugador recoge la caja de power-up."""
        pass  # player_has_powerup ya se pone a True en MatchScene

    def _on_powerup_activate(self):
        """El jugador pulsa E para lanzar un pelotazo si está cerca del balón."""

    # ─── BOUNDARIES & GOALS (idénticas a FirstScene) ─────────

    def _create_boundaries(self):
        w = self.world
        g = w.CreateStaticBody(position=(px2m(SW / 2), px2m(GROUND_Y)))
        g.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.6)

        c = w.CreateStaticBody(position=(px2m(SW / 2), px2m(-5)))
        c.CreatePolygonFixture(box=(px2m(SW / 2), px2m(5)), friction=0.2)

        wl = w.CreateStaticBody(position=(px2m(-5), px2m(GOAL_TOP_Y / 2)))
        wl.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

        wr = w.CreateStaticBody(position=(px2m(SW + 5), px2m(GOAL_TOP_Y / 2)))
        wr.CreatePolygonFixture(box=(px2m(5), px2m(GOAL_TOP_Y / 2)), friction=0.1)

    def _create_goals(self):
        return (self._make_goal('left'), self._make_goal('right'))

    def _make_goal(self, side):
        back_post_offset = 0
        gx = back_post_offset if side == 'left' else SW - back_post_offset
        cx = px2m(gx + GOAL_W / 2)

        # Travesaño superior
        bar = self.world.CreateStaticBody(
            position=(cx, px2m(GOAL_TOP_Y - GOAL_POST / 2))
        )
        bar.CreatePolygonFixture(
            box=(px2m(GOAL_W / 4), px2m(GOAL_POST / 2)),
            friction=0.3, restitution=0.4
        )

        # Palo trasero
        px_post = (gx - GOAL_POST / 2) if side == 'left' else (gx + GOAL_W + GOAL_POST / 2)
        back = self.world.CreateStaticBody(
            position=(px2m(px_post), px2m(GOAL_TOP_Y + GOAL_H / 2))
        )
        back.CreatePolygonFixture(
            box=(px2m(GOAL_POST / 2), px2m(GOAL_H / 2)),
            friction=0.3, restitution=0.4
        )

        # Suelo interior portería
        floor = self.world.CreateStaticBody(position=(cx, px2m(GROUND_Y)))
        floor.CreatePolygonFixture(box=(px2m(GOAL_W / 2), px2m(5)), friction=0.6)

        return pygame.Rect(gx, GOAL_TOP_Y, GOAL_W, GOAL_H)

    # ─── IA DEL BOSS ─────────────────────────────────────────

    def _update_boss_ai(self, delta_time):
        """Actualiza la IA de LaJenny: reloj interno + 1 TP por enfado + FSM."""
        if not (hasattr(self, 'boss') and self.boss.body
                and self.pelota.body and self.jugador.body):
            return

        # 1. Reloj interno (ciclo de enfado, 30s calmado / 12s enfadado)
        if hasattr(self.boss, 'update_logic'):
            self.boss.update_logic(delta_time)

        # 2. Rastrear transición enfadado → calmado para resetear flag de TP
        currently_angry = self.boss.is_angry
        if self._boss_was_angry and not currently_angry:
            self._teleport_used_this_anger = False
        self._boss_was_angry = currently_angry

        # 3. Intentar teletransporte SOLO si está enfadado y no lo ha usado este episodio
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

        # 4. FSM normal (movimiento)
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

        # Destruir todas las nubes activas
        if hasattr(self, 'clouds'):
            for c in self.clouds:
                self._destroy_cloud_body(c['body'])
            self.clouds            = []
            self.cloud_spawn_timer = CLOUD_SPAWN_INTERVAL * 0.3

        # Solo resetear el flag de TP si el boss ya NO está enfadado
        if not (hasattr(self, 'boss') and self.boss.is_angry):
            self._teleport_used_this_anger = False

        # _boss_was_angry debe reflejar el estado actual
        self._boss_was_angry = self.boss.is_angry if hasattr(self, 'boss') else False

        # Limpiar efectos visuales

    # ─── UPDATE ───────────────────────────────────────────────

    def update(self, delta_time):
        super().update(delta_time)

        # Aplicar impulsos de rebote de nubes DESPUÉS del world.Step (que ocurre en super)

        self._update_boss_ai(delta_time)

    # ─── RENDER ───────────────────────────────────────────────

    def _render_field(self, screen):
        # Fondo del estadio
        if not hasattr(self, '_stadium_bg'):
            try:
                bg = pygame.image.load('./assets/stadiums/stadium3_bg.png').convert()
                self._stadium_bg = pygame.transform.scale(bg, (SW, SH))
            except Exception:
                self._stadium_bg = pygame.Surface((SW, SH))
                self._stadium_bg.fill(BG_COLOR)
        screen.blit(self._stadium_bg, (0, 0))

        # Porterías fondo
        if not hasattr(self, '_goalpost_bg'):
            try:
                l_goalpost_bg    = pygame.image.load('./assets/stadiums/stadium-3-goalpost-bg.png').convert_alpha()
                r_goalpost_bg    = pygame.image.load('./assets/stadiums/stadium-3-goalpost-bg.png').convert_alpha()

                l_goalpost_bg_scaled = pygame.transform.scale(l_goalpost_bg, (GOAL_W*2, GOAL_H))
                r_goalpost_bg_scaled = pygame.transform.flip(l_goalpost_bg_scaled, True, False)
                
                self._goalpost_bg_l = l_goalpost_bg_scaled
                self._goalpost_bg_r = r_goalpost_bg_scaled
            except Exception:
                self._goalpost_bg_l = pygame.Surface((GOAL_W, GOAL_H), pygame.SRCALPHA)
                pygame.draw.rect(self._goalpost_bg_l, (*GOAL_NET_COLOR,), (0, 0, GOAL_W, GOAL_H))
                self._goalpost_bg_r = self._goalpost_bg_l.copy()
            self._goalpost_bg = True

        screen.blit(self._goalpost_bg_l, (0, GOAL_TOP_Y))
        screen.blit(self._goalpost_bg_r, (SW - GOAL_W*2, GOAL_TOP_Y))

    def _render_field_fg(self, screen):
        if not hasattr(self, '_goalpost_fg'):
            try:
                l_goalpost_fg    = pygame.image.load('./assets/stadiums/l_goalpost_fg.png').convert_alpha()
                r_goalpost_fg    = pygame.image.load('./assets/stadiums/r_goalpost_fg.png').convert_alpha()

                l_goalpost_fg_scaled = pygame.transform.scale(l_goalpost_fg, (GOAL_W*2, GOAL_H))
                r_goalpost_fg_scaled = pygame.transform.flip(l_goalpost_fg_scaled, True, False)

                self._goalpost_fg_l = l_goalpost_bg_scaled
                self._goalpost_fg_r = r_goalpost_bg_scaled
            except Exception:
                self._goalpost_fg_l = pygame.Surface((GOAL_W*2, GOAL_H), pygame.SRCALPHA)
                self._goalpost_fg_r = self._goalpost_fg_l.copy()
            self._goalpost_fg = True

        screen.blit(self._goalpost_fg_l, (0, GOAL_TOP_Y))
        screen.blit(self._goalpost_fg_r, (SW - GOAL_W*2, GOAL_TOP_Y))

    def render(self, screen):
        super().render(screen)
        self._draw_angry_indicator(screen)

    # ─── INDICADORES VISUALES ─────────────────────────────────

    def _draw_angry_indicator(self, screen):
        """Indicador de estado del boss (esquina superior derecha)."""
        if not hasattr(self, 'boss'):
            return

        if self.boss.is_angry:
            blink = (pygame.time.get_ticks() // 400) % 2 == 0
            color = ANGRY_INDICATOR_COLOR if blink else (200, 60, 30)
            tp_tag = " [TP USADO]" if self._teleport_used_this_anger else " [TP LISTO]"
            label  = "⚠ LA JENNY SE HA ENFADADO!" + tp_tag
            text   = self.angry_font.render(label, True, color)
        else:
            remaining_s = max(0, (30000 - self.boss.angry_timer) / 1000)
            label = f"La jenny está calmada  ({remaining_s:.0f}s)"
            text  = self.angry_font.render(label, True, (150, 255, 150))

        rect = text.get_rect(topright=ANGRY_INDICATOR_POS)
        bg   = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        screen.blit(bg, (rect.x - 8, rect.y - 4))
        screen.blit(text, rect)