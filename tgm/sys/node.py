from collections import defaultdict
from inspect import getmro


class NodeMeta(type):
    pass


class Node(object, metaclass=NodeMeta):
    """The base class for all objects in the scene graph."""
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args)
        obj._node_parent = None
        obj._node_children = set()
        obj._node_index = defaultdict(set)

        for key in getmro(type(obj)):
            obj.add_index_key(key, obj)

        return obj

    def add_index_key(self, key, node):
        """Register this object as having a given key."""
        if (self.parent() is not None) and (not self._node_index[key]):
            self.parent().add_index_key(key, self)

        self._node_index[key].add(node)

    def remove_index_key(self, key, node):
        """Unregister this object as having a given key."""
        self._node_index[key].remove(node)

        if (self.parent() is not None) and (not self._node_index[key]):
            self.parent().remove_index_key(key, self)

    def children(self, query):
        """Get all the immediate children of this object that fulfil the query.
        """
        if query is Node:
            return self._node_children.copy()

        raise NotImplemented()

    def parent(self, query=None):
        """Return the closest of the object's parents that satisfies the query.

        If no query is given then the object's direct parent will be returned.
        """
        if query is None or query is Node:
            return self._node_parent

        raise NotImplemented()

    def attach(self, node):
        """Add the given node as a child and update relevant indexes.

        This will detach the node from any parent it's currently attached to."""
        if node.parent() is not None:
            node.parent().detach(node)

        node._node_parent = self
        for key, node_set in node._node_index.items():
            if node_set:
                self.add_index_key(key, node)

        return node

    def detach(self, node):
        """Detach the given node from its parent and update relevant indexes."""
        for key, node_set in node._node_index.items():
            if node_set:
                self.remove_index_key(key, node)

        self._node_children.remove(node)
        node._node_parent = None

        return node

    def destroy(self):
        """Recursively destroy each of the object's children then destroy
        the object."""
        for child in self.children(Node):
            child.destroy()

        if self.parent() is not None:
            self.parent().detach(self)
