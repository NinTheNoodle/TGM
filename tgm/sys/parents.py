"""Builtin classifications for objects."""
from tgm.sys import Node


class Entity(Node):
    """The base class for corporeal objects.

    Conceptually an object is an entity if it exists in the world in
    some sense. Examples include obviously concrete things like
    the player character but also things like trigger zones and the points
    on a path. Basically anything that would easier useful to place in
    a scene rather than abstractly attach to an object."""
    pass


class Component(Node):
    """The base class for objects that enhance other objects.

    Conceptually an object is a component if it exists purely as an
    enhancement to another object. The idea being that if it makes more sense
    to abstractly attach this object to another object rather than place in
    a scene it is a component. Components should also do something, otherwise
    if the object is just data then the object should be a tag. An example is
    and enemy AI controller.
    """
    pass


class World(Node):
    """The base class for objects that logically encapsulate a universe.

    This object is intended to represent a level or some isolated universe.
    A useful example is using a separate world to hold the HUD in a game,
    since the HUD shouldn't interact with what it's overlaying and in a way
    exists in a separate universe to the level underneath. This concept can
    be extended, but the main idea being that objects in a world for the most
    part consider what's in the world to be all that exists."""
    pass


class Tag(Node):
    """The base class for objects that exist as information about their parent.

    Tag objects should be treated as pieces of information about an object.
    Whether an object is visible or solid can be determined by tags for example.
    Using tags over attributes has the advantages of being able to be indexed
    more easily, and not polluting the namespace of the class they are
    attached to."""
    pass


class Event(Node):
    """The base class for event objects."""
    # TODO: Doc string
    def __init__(self, func):
        super().__init__()
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
