import Box2D
from car import PlayerCar, Bulldozer, MotoMoto, LaJenny
from ball import Ball

class RocketFactory:
    @staticmethod
    def create_element(tipo, world, pos, subtipo=None):
        pos_m = (pos[0] / 10.0, pos[1] / 10.0)

        if tipo == "player":
            objeto = PlayerCar(pos)
            objeto.body = world.CreateDynamicBody(position=pos_m, fixedRotation=True)
            objeto.body.CreatePolygonFixture(
                box=(2, 1), density=objeto.mass, friction=0.3
            )
            return objeto

        elif tipo == "boss":
            boss_map = {
                'bulldozer': Bulldozer,
                'motomoto':  MotoMoto,
                'lajenny':   LaJenny,
            }
            # Para no crashear por un subtipo mal escrito
            cls = boss_map.get(subtipo, Bulldozer)
            objeto = cls(pos)
            objeto.body = world.CreateDynamicBody(position=pos_m, fixedRotation=True)
            objeto.body.CreatePolygonFixture(
                box=(2 * objeto.rect.width / 80, 1 * objeto.rect.height / 50),
                density=objeto.mass, friction=0.3
            )
            return objeto

        elif tipo == "ball":
            objeto = Ball(pos)
            objeto.body = world.CreateDynamicBody(position=pos_m)
            objeto.body.CreateCircleFixture(
                radius=1, density=0.5, friction=0.1, restitution=0.8
            )
            return objeto

        return None