from tgm.sys import Node


class Tag(Node):
    """The base class for objects that exist as information about their parent.

    Tag objects should be treated as pieces of information about an object.
    Whether an object is visible or solid can be determined by tags for example.

    Using tags over attributes has the advantages of being able to be indexed
    more easily, and not polluting the namespace of the class they are
    attached to.
    """
    pass
