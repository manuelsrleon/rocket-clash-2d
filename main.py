from director import Director
from menu import Menu

screen = None

if __name__ == "__main__":
    director = Director()
    scene = Menu(director)
    director.apilarEscena(scene)
    director.ejecutar()
