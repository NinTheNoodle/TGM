from tgm.sys import Node


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
