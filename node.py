class Node:
    def __init__(self, parent=None):
        self.transform = Transform(parent)
        self.children=[]
    def render(self):
        w = self.transform.world_transform()
        for c in self.children:
            c.render()