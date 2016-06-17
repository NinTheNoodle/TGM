from tgm.game import World, Layer
from tgm.sys import Entity


class Ground(Entity):
    pass


class Player(Entity):
    def __init__(self):
        super().__init__()
        print("hi")


def main():
    world = World()
    layer = world.attach(Layer())
    player = layer.attach(Player())
    print(player)

if __name__ == "__main__":
    main()
