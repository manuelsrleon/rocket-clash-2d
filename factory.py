import Box2D
from car import PlayerCar
from ball import Ball

class RocketFactory:
    @staticmethod
    def create_element(tipo, world, pos, subtipo=None):
        pos_m = (pos[0] / 10.0, pos[1] / 10.0) # Escala 10px = 1m

        if tipo == "player":
            objeto = PlayerCar(pos)
            objeto.body = world.CreateDynamicBody(position=pos_m, fixedRotation=True)
            # Caja de colisión ajustada al tamaño del coche
            objeto.body.CreatePolygonFixture(box=(1.2, 0.6), density=objeto.mass, friction=0.3)
            return objeto

        elif tipo == "ball":
            objeto = Ball(pos, scale=0.8) # Balón con tamaño corregido
            objeto.body = world.CreateDynamicBody(position=pos_m)
            # Círculo físico para el balón con rebote (restitution)
            objeto.body.CreateCircleFixture(radius=0.8, density=0.2, friction=0.1, restitution=0.8)
            return objeto
        return None