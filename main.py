from tgm.game import World, Layer
from tgm.sys import Entity, node_tree_summary, Component, on, Event


class SuperUpdate(Event):
    pass


class Ground(Entity):
    pass


class Player(Entity):
    def __init__(self):
        super().__init__()
        list(self._node_index[SuperUpdate])[0]()

    @on(SuperUpdate)
    def super_update(self):
        print("The legend never dies")


class Collider(Component):
    pass


def main():
    world = World()
    for i in range(20):
        layer = world.attach(Layer())
        for _ in range(1):
            player = layer.attach(Player())
            for _ in range(2):
                player.attach(Collider())
    print(node_tree_summary(world))
    for layer in world.find(Layer):
        print(layer.get_with(Collider))

if __name__ == "__main__":
    main()
