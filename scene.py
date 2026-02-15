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
