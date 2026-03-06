import pygame
from pygame.locals import *
from settings import ScreenSettings

# Estadísticas base para la física
DEFAULT_STATS = {'move_speed': 5.0, 'jump_force': 160.0, 'mass': 100.0, 'scale': 1.0}
BOSS1_STATS = {'move_speed': 10.0, 'jump_force': 70.0, 'mass': 0.8, 'scale': 0.9}

PLAYER_CAR_IMG = './assets/cars/player_car.png'
WHEEL_IMG      = './assets/cars/car_wheel.png'
BOSS1_IMG      = './assets/cars/bulldozer.png'

class MySprite(pygame.sprite.Sprite):
    def __init__(self, body_path, carPos=(0, 0), scale=1.0):
        super().__init__()
        try:
            body = pygame.image.load(body_path).convert_alpha()
        except:
            body = pygame.Surface((80, 50), pygame.SRCALPHA)
            body.fill((200, 50, 50))
        
        w, h = int(body.get_width() * scale), int(body.get_height() * scale)
        self.image = pygame.transform.scale(body, (w, h))
        self.rect = self.image.get_rect()
        self.establecerPosicion(carPos)
        self.body = None

    def establecerPosicion(self, pos):
        self.rect.centerx, self.rect.centery = int(pos[0]), int(pos[1])

class Car(MySprite):
    def __init__(self, body_path, carPos=(0, 0), stats=None):
        stats = stats or DEFAULT_STATS
        super().__init__(body_path, carPos, scale=stats.get('scale', 1.0))
        self.move_speed = stats.get('move_speed', DEFAULT_STATS['move_speed'])
        self.jump_force = stats.get('jump_force', DEFAULT_STATS['jump_force'])
        self.mass = stats.get('mass', DEFAULT_STATS['mass'])
        self.on_ground = False

    def jump(self):
        if self.on_ground and self.body:
            self.body.ApplyLinearImpulse(impulse=(0, -self.jump_force), point=self.body.worldCenter, wake=True)

    def move_left(self):
        if self.body: self.body.ApplyForce(force=(-self.move_speed * 10, 0), point=self.body.worldCenter, wake=True)

    def move_right(self):
        if self.body: self.body.ApplyForce(force=(self.move_speed * 10, 0), point=self.body.worldCenter, wake=True)

    def stop_horizontal(self):
        if self.body:
            vel = self.body.linearVelocity
            self.body.linearVelocity = (vel.x * 0.8, vel.y)

class PlayerCar(Car):
    def __init__(self, carPos=(100, 100)):
        super().__init__(PLAYER_CAR_IMG, carPos, stats=DEFAULT_STATS)
        self.moving_left = self.moving_right = False

    def handle_input(self, event_list):
        keys = pygame.key.get_pressed()
        self.moving_left = keys[K_a]
        self.moving_right = keys[K_d]
        
        for event in event_list:
            if event.type == KEYDOWN and event.key == K_w:
                self.jump()

        if self.moving_left: self.move_left()
        elif self.moving_right: self.move_right()
        else: self.stop_horizontal()

class Bulldozer(Car):
    def __init__(self, carPos=(600, 460)):
        self.stats_normal = {'move_speed': 4.0, 'jump_force': 60.0, 'mass': 3.0, 'scale': 1.5}
        # Bajamos la velocidad de 62.0 a 16.0. Sigue siendo más rápido que el jugador (12.0)
        self.stats_angry = {'move_speed': 16.0, 'jump_force': 60.0, 'mass': 4.5, 'scale': 1.5}
        
        super().__init__(BOSS1_IMG, carPos, stats=self.stats_normal)
        self.angry_timer = 0
        self.is_angry = False
        
        # ─── Estado inicial de la FSM ───
        self.state = "OFENSIVO"

    def update_logic(self, dt_ms):
        """Lógica interna: ciclos de enfado."""
        self.angry_timer += dt_ms
        if not self.is_angry and self.angry_timer > 5000:
            self.become_angry()
        elif self.is_angry and self.angry_timer > 15000:
            self.become_normal()

    def become_angry(self):
        self.is_angry = True
        self.angry_timer = 0
        self.move_speed = self.stats_angry['move_speed']

    def become_normal(self):
        self.is_angry = False
        self.angry_timer = 0
        self.move_speed = self.stats_normal['move_speed']

    def update_fsm(self, ball_pos, player_pos, goal_x_right):
        """
        Cerebro FSM del Bulldozer.
        (Reemplaza a decide_movement y apply_movement)
        Evalúa el entorno y decide hacia dónde aplicar fuerza física.
        """
        if not self.body:
            return

        my_pos = self.body.position
        
        # Distancias (en metros de Box2D)
        dist_to_goal = abs(ball_pos.x - goal_x_right)
        dist_to_player = abs(player_pos.x - my_pos.x)

        # ─── 1. TRANSICIONES DE ESTADO (FSM) ──────────────────
        if dist_to_goal < 25.0:
            # Si el balón está muy cerca de su portería, defiende a muerte
            self.state = "DEFENSIVO"
        elif self.is_angry:
            # Si se activa su Ultimate (manejado por update_logic), va a por el jugador
            self.state = "LOCO"
        else:
            # Por defecto, intenta atacar y marcar gol
            self.state = "OFENSIVO"

        # ─── 2. CÁLCULO DEL OBJETIVO FÍSICO (Target X) ──────────
        target_x = my_pos.x # Por defecto, frenar

        if self.state == "DEFENSIVO":
            # Va a posicionarse justo delante del balón para actuar de muro
            target_x = ball_pos.x + 2.0 
            
        elif self.state == "LOCO":
            # Va directo a las coordenadas del jugador para embestirlo
            target_x = player_pos.x
            
        elif self.state == "OFENSIVO":
            # Intenta empujar el balón hacia la izquierda
            if ball_pos.x < my_pos.x:
                target_x = ball_pos.x  # Acelera hacia el balón
            else:
                # Si el balón se queda atrás, retrocede un poco para rodearlo
                target_x = ball_pos.x + 4.0

       # ─── 3. MOTRICIDAD (Física Aplicada) ───────────────────
        current_max_speed = self.move_speed 
        
        # ¡NUEVO!: Boost de velocidad al defender (solo si no está ya en modo LOCO/Enfadado)
        if self.state == "DEFENSIVO" and not self.is_angry:
            current_max_speed = self.move_speed * 2.0  # El doble de rápido para llegar a salvar el gol
        
        # Diferencia entre dónde está y a dónde quiere ir
        diff = target_x - my_pos.x
        vel = self.body.linearVelocity

        # Margen muerto de 0.8 metros para que no vibre
        if abs(diff) > 0.8:
            target_vx = current_max_speed if diff > 0 else -current_max_speed
        else:
            target_vx = 0.0

        # BLEND FÍSICO (Inercia): Simula el peso del Bulldozer
        blend_factor = 0.15 
        new_vx = vel.x + (target_vx - vel.x) * blend_factor
        
        # Aplicamos la velocidad resultante al chasis de Box2D
        self.body.linearVelocity = (new_vx, vel.y)

        # ─── 4. ESTADO SALTO (Reflejo Concurrente) ────────────
        dist_x_ball = abs(ball_pos.x - my_pos.x)
        if dist_x_ball < 4.0 and ball_pos.y < my_pos.y - 2.0 and self.on_ground:
            self.jump()

    def apply_movement(self, target_x, ball_pos, player_pos,
                       boss_speed=6.0, boss_speed_angry=9.0, boss_blend=0.18,
                       boss_chase_margin=0.3):
        """Aplica el movimiento hacia el objetivo."""
        if not self.body:
            return

        speed = boss_speed_angry if self.is_angry else boss_speed
        diff = target_x - self.body.position.x
        vel = self.body.linearVelocity

        if abs(diff) > boss_chase_margin:
            target_vx = speed if diff > 0 else -speed
        else:
            target_vx = 0.0

        new_vx = vel.x + (target_vx - vel.x) * boss_blend
        self.body.linearVelocity = (new_vx, vel.y)

        # Saltar si el objetivo está por encima
        target_y = ball_pos.y
        if target_y < self.body.position.y - 3.0 and abs(diff) < 8.0:
            if self.on_ground:
                self.jump()

#TODO: clases fantasma. definidas para que el factory.py pueda instanciarlas sin errores, pero no tienen lógica ni assets propios.
class MotoMoto(Car):
    """Boss del escenario 2: pequeño y rápido. Se teletransporta a la portería si el balón está cerca."""

    def __init__(self, carPos=(600, 460)):
        self.stats_normal = {'move_speed': 7.0, 'jump_force': 55.0, 'mass': 1.5, 'scale': 0.8}
        self.stats_angry = {'move_speed': 22.0, 'jump_force': 55.0, 'mass': 2.0, 'scale': 0.8}

        super().__init__(BOSS1_IMG, carPos, stats=self.stats_normal)
        self.angry_timer = 0
        self.is_angry = False

        # FSM
        self.state = "OFENSIVO"

        # Teletransporte
        self.teleport_cooldown = 0       # ms restantes de cooldown
        self.teleport_cooldown_max = 4000 # ms entre teletransportes
        self.teleport_range = 20.0       # distancia (m) del balón a portería para activar TP

    def update_logic(self, dt_ms):
        """Lógica interna: ciclos de enfado y cooldown de teletransporte."""
        self.angry_timer += dt_ms
        if not self.is_angry and self.angry_timer > 30000:   # 30 segundos calmado
            self.become_angry()
        elif self.is_angry and self.angry_timer > 12000:
            self.become_normal()

        # Reducir cooldown de TP
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt_ms
            if self.teleport_cooldown < 0:
                self.teleport_cooldown = 0

    def become_angry(self):
        self.is_angry = True
        self.angry_timer = 0
        self.move_speed = self.stats_angry['move_speed']

    def become_normal(self):
        self.is_angry = False
        self.angry_timer = 0
        self.move_speed = self.stats_normal['move_speed']

    def try_teleport_to_goal(self, ball_pos, goal_x, goal_y):
        """
        Si el balón está muy cerca de la portería y el cooldown lo permite,
        se teletransporta delante de la portería.
        Devuelve True si se teletransportó.
        """
        if not self.body:
            return False
        if self.teleport_cooldown > 0:
            return False

        dist_ball_goal = abs(ball_pos.x - goal_x)
        if dist_ball_goal < self.teleport_range:
            # Teletransportarse justo delante de la portería
            tp_x = goal_x + (2.0 if ball_pos.x < goal_x else -2.0)
            self.body.position = (tp_x, goal_y)
            self.body.linearVelocity = (0, 0)
            self.teleport_cooldown = self.teleport_cooldown_max
            return True
        return False

    def update_fsm(self, ball_pos, player_pos, goal_x_right):
        """
        Cerebro FSM de MotoMoto.
        Similar al Bulldozer pero más agresivo y con teletransporte.
        """
        if not self.body:
            return

        my_pos = self.body.position

        # Distancias
        dist_to_goal = abs(ball_pos.x - goal_x_right)
        dist_to_player = abs(player_pos.x - my_pos.x)

        # ─── 1. TRANSICIONES DE ESTADO ────────────────────────
        if dist_to_goal < 25.0:
            self.state = "DEFENSIVO"
        elif self.is_angry:
            self.state = "LOCO"
        else:
            self.state = "OFENSIVO"

        # ─── 2. CÁLCULO DEL OBJETIVO (Target X) ──────────────
        target_x = my_pos.x

        if self.state == "DEFENSIVO":
            target_x = ball_pos.x + 1.5
        elif self.state == "LOCO":
            target_x = player_pos.x
        elif self.state == "OFENSIVO":
            if ball_pos.x < my_pos.x:
                target_x = ball_pos.x
            else:
                target_x = ball_pos.x + 3.0

        # ─── 3. MOTRICIDAD ────────────────────────────────────
        current_max_speed = self.move_speed

        if self.state == "DEFENSIVO" and not self.is_angry:
            current_max_speed = self.move_speed * 2.5

        diff = target_x - my_pos.x
        vel = self.body.linearVelocity

        if abs(diff) > 0.5:
            target_vx = current_max_speed if diff > 0 else -current_max_speed
        else:
            target_vx = 0.0

        # Blend más agresivo (menos inercia, más ágil)
        blend_factor = 0.22
        new_vx = vel.x + (target_vx - vel.x) * blend_factor
        self.body.linearVelocity = (new_vx, vel.y)

        # ─── 4. SALTO ────────────────────────────────────────
        dist_x_ball = abs(ball_pos.x - my_pos.x)
        if dist_x_ball < 3.5 and ball_pos.y < my_pos.y - 1.5 and self.on_ground:
            self.jump()


class LaJenny(Car):
    FLASH_INTERVAL = 20000   # tiempo recarga flash (ms)
    FLASH_DURATION = 900    # animacion de flash en ms
    FLASH_RANGE_X = 35.0   # en metros

    def __init__(self, carPos=(600, 460)):
        self._jenny_stats = {'move_speed': 16.0, 'jump_force': 350.0, 'mass': 0.9, 'scale': 1.1}
        # TODO: Cambiar PLAYER_CAR_IMG por una imagen específica de Jenny
        super().__init__(PLAYER_CAR_IMG, carPos, stats=self._jenny_stats)

        # Temporizador de flash
        self._flash_timer = int(self.FLASH_INTERVAL * 0.6)
        self.is_flashing = False 
        self._flash_vis_timer = 0
        self.state = "OFENSIVO"

    def update_logic(self, dt_ms):
        self._flash_timer += dt_ms

        if self.is_flashing:
            self._flash_vis_timer -= dt_ms
            if self._flash_vis_timer <= 0:
                self.is_flashing = False
                self._flash_vis_timer = 0

    def should_flash(self):
        return self._flash_timer >= self.FLASH_INTERVAL

    def trigger_flash(self):
        self.is_flashing = True
        self._flash_vis_timer = self.FLASH_DURATION
        self._flash_timer = 0

    def can_reach_player(self, player_pos):
        if not self.body:
            return False
        my_x = self.body.position.x
        dist = my_x - player_pos.x
        return 0 < dist < self.FLASH_RANGE_X
    
    # state machine logic
    def update_fsm(self, ball_pos, player_pos, goal_x_right):
        if not self.body:
            return

        my_pos = self.body.position
        dist_to_goal = abs(ball_pos.x - goal_x_right)

        if dist_to_goal < 20.0:
            self.state = "DEFENSIVO"
        else:
            self.state = "OFENSIVO"

        if self.state == "DEFENSIVO":
            target_x = ball_pos.x + 2.0
        else:
            if ball_pos.x < my_pos.x:
                target_x = ball_pos.x
            else:
                target_x = ball_pos.x + 3.0

        diff = target_x - my_pos.x
        vel  = self.body.linearVelocity

        if abs(diff) > 0.8:
            target_vx = self.move_speed if diff > 0 else -self.move_speed
        else:
            target_vx = 0.0

        new_vx = vel.x + (target_vx - vel.x) * 0.18
        self.body.linearVelocity = (new_vx, vel.y)

        # jump if ball is above and close
        if abs(ball_pos.x - my_pos.x) < 4.0 and ball_pos.y < my_pos.y - 2.0 and self.on_ground:
            self.jump()