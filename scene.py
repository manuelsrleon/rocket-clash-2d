import pygame

class Scene:
    
    def __init__(self, director):
        self.director = director

    def update(self, *args):
        raise NotImplemented("Update method not implemented.")

    def events(self, *args):
        raise NotImplemented("Events method not implemented.")

    def render(self, *args):
        raise NotImplemented("Render method not implemented.")


class PyGameScene(Scene):
    
    def __init__(self, director):
        Scene.__init__(self, director)
        # The Director is responsible for initializing pygame and the screen.
        # Scenes declare a screen attribute which the Director will assign.
        self.screen = None
        # If True, the scene below will also be rendered
        self.is_overlay = False

        # --- SISTEMA DE TRANSICIÓN ---
        self.fade_alpha = 0
        self.fade_speed = 150  # Velocidad de cambio de alpha por segundo
        self.fade_mode = None  # Puede ser "IN", "OUT" o None
        self.on_fade_complete = None

        # Superficie negra persistente para el efecto
        # Se inicializa con el tamaño de la pantalla del director
        sw, sh = director.screen.get_size() if director.screen else (800, 600)
        self.fade_surf = pygame.Surface((sw, sh))
        self.fade_surf.fill((0, 0, 0))

    def fade_to_black(self, callback=None):
        """Inicia el fundido hacia negro total."""
        self.fade_mode = "IN"
        self.on_fade_complete = callback

    def fade_from_black(self):
        """Inicia el fundido desde negro hacia la visibilidad."""
        self.fade_alpha = 255
        self.fade_mode = "OUT"

    def update_fade(self, dt_ms):
        """Calcula el nivel de transparencia basado en el delta_time."""
        if not self.fade_mode:
            return

        dt_sec = dt_ms / 1000.0
        if self.fade_mode == "IN":
            self.fade_alpha = min(self.fade_alpha + self.fade_speed * dt_sec, 255)
            if self.fade_alpha >= 255 and self.on_fade_complete:
                self.on_fade_complete()
                self.on_fade_complete = None # Limpiar para evitar doble llamada
        
        elif self.fade_mode == "OUT":
            self.fade_alpha = max(self.fade_alpha - self.fade_speed * dt_sec, 0)
            if self.fade_alpha <= 0:
                self.fade_mode = None

    def draw_fade(self, screen):
        """Dibuja la capa negra superpuesta con el alpha actual."""
        if self.fade_alpha > 0:
            self.fade_surf.set_alpha(int(self.fade_alpha))
            screen.blit(self.fade_surf, (0, 0))