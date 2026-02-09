
import Car;

class Scene:
    def __init__(self, director):
        self.director = director
    def update(self, *args):
        raise NotImplemented("Update method not implemented.")
    def events(self, *args):
        raise NotImplemented("Events method not implemented.")
    def render(self, *args):
        raise NotImplemented("Render method not implemented.")
    
: 

class PyGameScene(Scene):
    def __init__(self, director): 
        Scene.__init__(self, director)
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))