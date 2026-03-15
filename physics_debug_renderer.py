import pygame
from Box2D import b2Draw, b2DrawExtended, b2CircleShape

LINE_WIDTH = 2
class PhysicsDebugRenderer(b2DrawExtended):
    """
    This debug draw class accepts callbacks from Box2D (which specifies what to draw)
    and handles all of the rendering.

    If you are writing your own game, you likely will not want to use debug drawing.
    Debug drawing, as its name implies, is for debugging.
    """
    surface = None
    world = None
    def __init__(self, test=None, world=None, surface=None, **kwargs):
        b2DrawExtended.__init__(self, **kwargs)
        self.flipX = False
        self.flipY = True
        self.convertVertices = True
        self.test = test
        self.surface = surface
        self.world = world

    def render(self):
        for body in self.world.bodies:
            pos = body.position
            for fixture in body.fixtures: 
                if isinstance(fixture.shape, b2CircleShape):
                    self.world.renderer.DrawCircle(pos, fixture.shape.radius, pygame.Color(255,0,0))
                else:
                    print(fixture.shape.vertices)
                    self.world.renderer.DrawPolygon(
                        [tuple(((vertex[0] + pos[0])*10, (vertex[1]+pos[1])*10)) for vertex in fixture.shape.vertices], pygame.Color(255,0,0,255))

    def StartDraw(self):
        self.zoom = self.test.viewZoom
        self.center = self.test.viewCenter
        self.offset = self.test.viewOffset
        self.screenSize = self.test.screenSize

    def EndDraw(self):
        pass

    def DrawPoint(self, p, size, color):
        """
        Draw a single point at point p given a pixel size and color.
        """
        self.DrawCircle(p, size / self.zoom, color, drawwidth=0)

    def DrawAABB(self, aabb, color):
        """
        Draw a wireframe around the AABB with the given color.
        """
        points = [(aabb.lowerBound.x, aabb.lowerBound.y),
                  (aabb.upperBound.x, aabb.lowerBound.y),
                  (aabb.upperBound.x, aabb.upperBound.y),
                  (aabb.lowerBound.x, aabb.upperBound.y)]

        pygame.draw.aalines(self.surface, color, True, points)

    def DrawSegment(self, p1, p2, color):
        """
        Draw the line segment from p1-p2 with the specified color.
        """
        pygame.draw.aaline(self.surface, color, p1, p2)

    def DrawTransform(self, xf):
        """
        Draw the transform xf on the screen
        """
        p1 = xf.position
        p2 = self.to_screen(p1 + self.axisScale * xf.R.x_axis)
        p3 = self.to_screen(p1 + self.axisScale * xf.R.y_axis)
        p1 = self.to_screen(p1)
        pygame.draw.aaline(self.surface, (255, 0, 0), p1, p2)
        pygame.draw.aaline(self.surface, (0, 255, 0), p1, p3)

    def DrawCircle(self, center, radius, color):
        """
        Draw a wireframe circle given the center, radius, axis of orientation
        and color.
        """
        radius *= self.zoom
        if radius < 1:
            radius = 1
        else:
            radius = int(radius)

        pygame.draw.circle(self.surface, color,
                           (center.x*10,center.y*10), radius*10, LINE_WIDTH)

    def DrawSolidCircle(self, center, radius, axis, color):
        """
        Draw a solid circle given the center, radius, axis of orientation and
        color.
        """
        radius *= self.zoom
        if radius < 1:
            radius = 1
        else:
            radius = int(radius)

        pygame.draw.circle(self.surface, (color / 2) + [127],
                           center, radius, 0)
        pygame.draw.circle(self.surface, color, center, radius, LINE_WIDTH)
        pygame.draw.aaline(self.surface, (255, 0, 0), center,
                           (center[0] - radius * axis[0],
                            center[1] + radius * axis[1]))

    def DrawPolygon(self, vertices, color):
        """
        Draw a wireframe polygon given the screen vertices with the specified color.
        """
        if not vertices:
            return

        if len(vertices) == 2:
            pygame.draw.aaline(self.surface, color,
                               vertices[0], vertices)
        else:
            pygame.draw.polygon(self.surface, color, vertices, LINE_WIDTH)

    def DrawSolidPolygon(self, vertices, color):
        """
        Draw a filled polygon given the screen vertices with the specified color.
        """
        if not vertices:
            return

        if len(vertices) == 2:
            pygame.draw.aaline(self.surface, color,
                               vertices[0], vertices[1])
        else:
            pygame.draw.polygon(
                self.surface, (color / 2) + [127], vertices, 0)
            pygame.draw.polygon(self.surface, color.bytes, vertices, 1)