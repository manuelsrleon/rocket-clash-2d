import Box2D
import pygame
from car import PlayerCar, Bulldozer, MotoMoto, LaJenny
from ball import Ball

# PPM compartido con match_scene.py
PPM = 10.0

def px2m(px): return px / PPM
def m2px(m):  return m  * PPM


class RocketFactory:
    @staticmethod
    def create_element(tipo, world, pos, subtipo=None):
        pos_m = (pos[0] / PPM, pos[1] / PPM)

        if tipo == "player":
            objeto = PlayerCar(pos)
            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                fixedRotation=False,
                linearDamping=0.3
            )
            objeto.body.CreatePolygonFixture(
                box=(3.85, 0.5, (0.0, 0.5), 0),
                density=10.0,
                friction=0.08,
                restitution=0.1
            )
            objeto.body.CreatePolygonFixture(
                vertices=[(-3.0, -1.0), (0.0, -1.0), (0.5, 0.0), (-3.9, 0.0)],
                density=10.0,
                friction=0.0,
                restitution=0.1
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
            hw = objeto.rect.width  / 2 / PPM
            hh = objeto.rect.height / 2 / PPM
            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                fixedRotation=False,
                linearDamping=0.5
            )
            objeto.body.CreatePolygonFixture(
                box=(hw, hh / 2, (0, hh / 2), 0),
                density=objeto.mass, friction=0.08, restitution=0.12
            )
            return objeto

        elif tipo == "ball":
            objeto = Ball(pos)
            objeto.body = world.CreateDynamicBody(
                position=pos_m,
                linearDamping=0.08,     # menos resistencia al aire → conserva velocidad
                angularDamping=0.3
            )
            objeto.body.CreateCircleFixture(
                radius=3,
                density=0.05,           # mucho más ligero → reacciona más al contacto
                friction=0.5,
                restitution=0.9       # rebota más en general
            )
            return objeto

        return None

    # ─── BOUNDARIES ───────────────────────────────────────────

    @staticmethod
    def create_boundaries(world, screen_width, ground_y, goal_top_y):
        """Crea los cuerpos estáticos del campo: suelo, techo y paredes laterales.
        Devuelve una lista de bodies creados (por si se necesitan destruir)."""
        bodies = []

        # Suelo
        g = world.CreateStaticBody(position=(px2m(screen_width / 2), px2m(ground_y)))
        g.CreatePolygonFixture(box=(px2m(screen_width / 2), px2m(5)), friction=0.6)
        bodies.append(g)

        # Techo
        c = world.CreateStaticBody(position=(px2m(screen_width / 2), px2m(-5)))
        c.CreatePolygonFixture(box=(px2m(screen_width / 2), px2m(5)), friction=0.2)
        bodies.append(c)

        # Pared izquierda (solo hasta el top de la portería)
        wl = world.CreateStaticBody(position=(px2m(-5), px2m(goal_top_y / 2)))
        wl.CreatePolygonFixture(box=(px2m(5), px2m(goal_top_y / 2)), friction=0.1)
        bodies.append(wl)

        # Pared derecha
        wr = world.CreateStaticBody(position=(px2m(screen_width + 5), px2m(goal_top_y / 2)))
        wr.CreatePolygonFixture(box=(px2m(5), px2m(goal_top_y / 2)), friction=0.1)
        bodies.append(wr)

        return bodies

    # ─── GOALS ────────────────────────────────────────────────

    @staticmethod
    def create_goal(world, side, screen_width, ground_y, goal_w, goal_h, goal_post, goal_top_y, goal_x):
        """Crea una portería (travesaño, palo trasero, suelo interior).
        Devuelve un pygame.Rect que representa la zona de gol."""
        gx = 0 if side == 'left' else screen_width - goal_w
        cx = px2m(gx + goal_w / 2)

        # Travesaño superior
        bar = world.CreateStaticBody(
            position=(cx, px2m(goal_top_y - goal_post / 2))
        )
        bar.CreatePolygonFixture(
            box=(px2m(goal_w / 2), px2m(goal_post / 2)),
            friction=0.3, restitution=0.4
        )

        # Palo trasero
        px_post = (gx - goal_post / 2) if side == 'left' else (gx + goal_w + goal_post / 2)
        back = world.CreateStaticBody(
            position=(px2m(px_post), px2m(goal_top_y + goal_h / 2))
        )
        back.CreatePolygonFixture(
            box=(px2m(goal_post / 2), px2m(goal_h / 2)),
            friction=0.3, restitution=0.4
        )

        # Suelo interior portería
        floor = world.CreateStaticBody(position=(goal_x, px2m(ground_y)))
        floor.CreatePolygonFixture(box=(px2m(goal_w / 2), px2m(5)), friction=0.6)

        return (pygame.Rect(goal_x, goal_top_y, goal_w, goal_h),pygame.Rect(goal_x, goal_top_y, goal_w, goal_h))

    @staticmethod
    def create_goals(world, screen_width, ground_y, goal_w, goal_h, goal_post, goal_top_y, goal_x, goal_y):
        """Crea ambas porterías. Devuelve (rect_left, rect_right)."""
        rect_l = RocketFactory.create_goal(
            world, 'left', screen_width, ground_y, goal_w, goal_h, goal_post, goal_top_y, goal_x
        )
        rect_r = RocketFactory.create_goal(
            world, 'right', screen_width, ground_y, goal_w, goal_h, goal_post, goal_top_y, goal_x
        )
        return (rect_l, rect_r)

    # ─── MUD (FirstScene) ────────────────────────────────────

    @staticmethod
    def create_mud(world, x_px, w_px, ground_y, mud_height):
        """Crea un cuerpo sensor estático de barro. Devuelve el body Box2D."""
        cx_m = px2m(x_px + w_px / 2)
        cy_m = px2m(ground_y - mud_height / 2)
        hw_m = px2m(w_px / 2)
        hh_m = px2m(mud_height / 2)

        body = world.CreateStaticBody(position=(cx_m, cy_m))
        body.CreatePolygonFixture(
            box=(hw_m, hh_m),
            isSensor=True,
            userData={'type': 'mud'}
        )
        return body

    @staticmethod
    def destroy_body(world, body):
        """Destruye un body Box2D de forma segura."""
        if body:
            try:
                world.DestroyBody(body)
            except Exception:
                pass

    # ─── CLOUDS (SecondScene) ─────────────────────────────────

    @staticmethod
    def create_cloud(world, x_px, y_px, w_px, h_px, friction=0.0, restitution=3.0):
        """Crea un cuerpo estático de nube con alto rebote. Devuelve el body Box2D."""
        cx_m = px2m(x_px + w_px / 2)
        cy_m = px2m(y_px + h_px / 2)
        hw_m = px2m(w_px / 2)
        hh_m = px2m(h_px / 2)

        body = world.CreateStaticBody(position=(cx_m, cy_m))
        body.CreatePolygonFixture(
            box=(hw_m, hh_m),
            friction=friction,
            restitution=restitution,
            userData={'type': 'cloud'}
        )
        return body

    # ─── TRAPDOORS (ThirdScene) ───────────────────────────────

    @staticmethod
    def create_trapdoor_sensor(world, cx_px, y_px, w_px, h_px, index):
        """Crea un sensor estático para una trapdoor. Devuelve el body Box2D."""
        body = world.CreateStaticBody(
            position=(px2m(cx_px), px2m(y_px + h_px / 2))
        )
        body.CreatePolygonFixture(
            box=(px2m(w_px / 2), px2m(h_px / 2)),
            isSensor=True,
            userData={'type': 'trapdoor', 'index': index}
        )
        return body

    # ─── POWER-UP BOX ─────────────────────────────────────────

    @staticmethod
    def create_powerup_body(world, x_px, size_px):
        """Crea un body cinemático sensor para la caja de power-up.
        Devuelve el body Box2D."""
        cx_m = px2m(x_px)
        cy_m = px2m(-size_px)  # empieza fuera de pantalla
        body = world.CreateKinematicBody(position=(cx_m, cy_m))
        body.CreatePolygonFixture(
            box=(px2m(size_px / 2), px2m(size_px / 2)),
            isSensor=True,
            userData={'type': 'powerup'}
        )
        return body