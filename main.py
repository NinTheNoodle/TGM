from tgm.game import World, Layer
from tgm.sys import Entity, node_tree_summary, Component, on, Event, Query, Node
import cProfile
import pstats
from random import randint


class SuperUpdate(Event):
    pass


class Ground(Entity):
    pass

blah = True

class Player(Entity):
    def __init__(self):
        global blah
        super().__init__()
        self.r = blah
        blah = not blah
        list(self._node_index[SuperUpdate])[0]()

    @on(SuperUpdate)
    def super_update(self):
        pass# print("The legend never dies")


class Collider(Component):
    pass


class Dummy:
    pass


def main():
    world = World()
    for i in range(100):
        layer = world.attach(Layer())
        for _ in range(1):
            player = layer.attach(Player())
            for _ in range(1):
                player.attach(Collider())
    print(node_tree_summary(world))

    print(world)

    print(list(world.find(Player[SuperUpdate])))

    print(list(
        world.find(Collider, trim=Node["r", lambda x: x.r])
    ))

    Query(Node,
          child_query=Query(Collider),
          condition=lambda x: hasattr(x, "r") and getattr(x, "r"))

    # world = None
    #
    # def profile():
    #     nonlocal world
    #     for _ in range(1):
    #         world = World()
    #         for i in range(10):
    #             layer = world.attach(Layer())
    #             for _ in range(5000):
    #                 player = layer.attach(Player())
    #                 for _ in range(2):
    #                     player.attach(Collider())
    #
    # pr = cProfile.Profile()
    #
    # pr.runcall(profile)
    # pr.create_stats()
    # stats = pstats.Stats(pr)
    # stats.print_stats(100)
    # print(node_tree_summary(world))


if __name__ == "__main__":
    main()
