from tgm.sys import Node


class World(Node):
    """The base class for objects that logically encapsulate a universe.

    This object is intended to represent a level or some isolated universe.
    A useful example is using a separate world to hold the HUD in a game,
    since the HUD shouldn't interact with what it's overlaying and in a way
    exists in a separate universe to the level underneath. This concept can
    be extended, but the main idea being that objects in a world for the most
    part consider what's in the world to be all that exists."""
    pass
