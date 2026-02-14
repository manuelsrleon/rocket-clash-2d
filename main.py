from director import Director
from menu import Menu

# Legacy global screen variable (not currently used)
screen = None

if __name__ == "__main__":
    director = Director()
    scene = Menu(director)
    director.apilarEscena(scene)
    director.ejecutar()
