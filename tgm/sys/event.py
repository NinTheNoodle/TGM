"""Builtin classifications for objects."""
from tgm.sys import Node, add_instantiation_call
from functools import partial


class Event(Node):
    """The base class for event objects."""
    def __init__(self, func):
        super().__init__()
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def on(event_type):
    """Register the function to be called during the given event."""
    def _event_wrap(func):
        def _attach_event(obj):
            obj.attach(event_type(partial(func, obj)))

        add_instantiation_call(func, _attach_event)
        return func
    return _event_wrap
