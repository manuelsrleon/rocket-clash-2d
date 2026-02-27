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
            # Hitbox de 2 fixtures ajustada píxel a píxel al sprite (78×20 px, PPM=10):
            # El body.position corresponde al rect.center del sprite (centro geométrico).
            # En coordenadas locales del body: Y+ apunta hacia abajo (igual que pantalla).

            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                fixedRotation=True,
                linearDamping=0.3
            )

            # Fixture 1 – Chasis inferior (rectángulo completo, zona de ruedas)
            # Extiende de y=0.0 a y=+1.0 m (borde inferior exacto del sprite 20px)
            objeto.body.CreatePolygonFixture(
                box=(3.85, 0.5, (0.0, 0.5), 0),
                density=0.09,
                friction=0.08,
                restitution=0.12
            )

            # Fixture 2 – Cabina superior (trapezoide, zona del habitáculo/capó)
            # vértices medidos del mapa de píxeles (coords locales Y-down):
            #   techo:   x[-3.0..+0.0]  y=-1.0
            #   base:    x[-3.9..+0.5]  y= 0.0  (fusiona con chasis sin hueco)
            objeto.body.CreatePolygonFixture(
                vertices=[(-3.0, -1.0), (0.0, -1.0), (0.5, 0.0), (-3.9, 0.0)],
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