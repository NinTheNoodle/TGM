from tgm.sys import Node


class World(Node):
    pass


class Layer(Node):
    pass


class Ground(Node):
    pass


class Player(Node):
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
