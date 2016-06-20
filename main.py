from tgm.game import World, Layer
from tgm.sys import Entity, node_tree_summary, Component
from random import randint

class Ground(Entity):
    pass


class Player(Entity):
    def __init__(self):
        super().__init__()
        #print("hi")


class Collider(Component):
    pass


def main():
    world = World()
    for i in range(20):
        layer = world.attach(Layer())
        for _ in range(4):
            player = layer.attach(Player())
            for _ in range(1 + i % 2):
                player.attach(Collider())
    print(node_tree_summary(world))

if __name__ == "__main__":
    main()
