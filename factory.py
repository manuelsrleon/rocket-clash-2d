import Box2D
from car import PlayerCar, Bulldozer, MotoMoto, LaJenny
from ball import Ball

# PPM compartido con match_scene.py
PPM = 10.0

class RocketFactory:
    @staticmethod
    def create_element(tipo, world, pos, subtipo=None):
        pos_m = (pos[0] / PPM, pos[1] / PPM)

        if tipo == "player":
            objeto = PlayerCar(pos)
            # Hitbox proporcional al sprite (140×70 px → 14×7 m → half 7×3.5)
            # density baja para masa razonable: 14*7*0.08 = 7.84
            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                fixedRotation=True,
                linearDamping=0.5
            )
            objeto.body.CreatePolygonFixture(
                box=(7.0, 3.5),
                density=0.08,
                friction=0.4,
                restitution=0.05
            )
            return objeto

        elif tipo == "boss":
            boss_map = {
                'bulldozer': Bulldozer,
                'motomoto':  MotoMoto,
                'lajenny':   LaJenny,
            }
            cls = boss_map.get(subtipo, Bulldozer)
            objeto = cls(pos)
            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                fixedRotation=True,
                linearDamping=0.5
            )
            objeto.body.CreatePolygonFixture(
                box=(2 * objeto.rect.width / 80, 1 * objeto.rect.height / 50),
                density=objeto.mass, friction=0.3
            )
            return objeto

        elif tipo == "ball":
            objeto = Ball(pos)
            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                linearDamping=0.3,
                angularDamping=0.4
            )
            # ball.png = 50×50 px → radio 25px → 2.5m
            objeto.body.CreateCircleFixture(
                radius=2.5,
                density=0.3,
                friction=0.5,
                restitution=0.7
            )
            return objeto

        return None
    
    @staticmethod
    def create_mud(world, pos, size=(40, 20)):
        pos_m = (pos[0] / 10.0, pos[1] / 10.0)
        mud_body = world.CreateStaticBody(position=pos_m)
        # isSensor=True hace que no haya choque físico, solo detección
        mud_body.CreatePolygonFixture(box=(size[0]/20, 
                                      size[1]/20), 
                                      isSensor=True, 
                                      userData={'type': 'mud'})
        return mud_body