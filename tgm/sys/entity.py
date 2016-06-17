from tgm.sys import Node


class Entity(Node):
    """The base class for corporeal objects.

    Conceptually an object is an entity if it exists in the world in
    some sense. Examples include obviously concrete things like
    the player character but also things like trigger zones and the points
    on a path. Basically anything that would easier useful to place in
    a scene rather than abstractly attach to an object."""
    pass
