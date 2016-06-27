from tgm.game import World, Layer
from tgm.sys import Entity, node_tree_summary, Component, on, Event, Query
import cProfile
import pstats


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
        pass# print("The legend never dies")


class Collider(Component):
    pass


def main():
    world = World()
    for i in range(100):
        layer = world.attach(Layer())
        for _ in range(1):
            player = layer.attach(Player())
            for _ in range(1):
                player.attach(Collider())
    # print(node_tree_summary(world))

    def profile():
        for _ in range(60000):
            player.get(Query(Collider))

    pr = cProfile.Profile()

    pr.runcall(profile)
    pr.create_stats()
    stats = pstats.Stats(pr)
    stats.print_stats(100)


if __name__ == "__main__":
    main()
