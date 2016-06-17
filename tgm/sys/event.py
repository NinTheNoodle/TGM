"""Builtin classifications for objects."""
from tgm.sys import Node


class Event(Node):
    """The base class for event objects."""
    # TODO: Doc string
    def __init__(self, func):
        super().__init__()
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
