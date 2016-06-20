from collections import defaultdict, Counter
from inspect import getmro, getmembers
from tgm.sys import Query


class NodeMeta(type):
    pass


class Node(metaclass=NodeMeta):
    """The base class for all objects in the scene graph."""
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj._node_parent = None
        obj._node_children = set()
        obj._node_index = defaultdict(set)

        # Register each base class in the index of the created object
        for key in getmro(type(obj)):
            obj.add_index_key(key, obj)

        for call in _get_instantiation_calls(cls):
            call(obj)

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

    def matches(self, query):
        if not isinstance(query, Query):
            query = Query(query)

        return query.matches(self)

    def parent(self, query=None):
        """Return the closest of the object's parents that satisfies the query.

        If no query is given then the object's direct parent will be returned.
        """
        if query is None or query is Node:
            return self._node_parent

        if not isinstance(query, Query):
            query = Query(query)

        parent = self._node_parent
        while parent is not None:
            if query.matches(parent):
                return parent
            parent = parent._node_parent

        raise ValueError("No parent found matching the given query")

    def children(self, query):
        """Get all the immediate children of this object that fulfil the query.
        """
        if query is Node:
            return self._node_children.copy()

        if not isinstance(query, Query):
            query = Query(query)

        return query.find_on(self)

    def children_with(self, query):
        if not isinstance(query, Query):
            query = Query(query)

        return Query(Node).with_child(query).find_on(self)

    def find(self, query):
        if not isinstance(query, Query):
            query = Query(query)

        return query.find_in(self)

    def find_with(self, query):
        if not isinstance(query, Query):
            query = Query(query)

        return Query(Node).with_child(query).find_in(self)

    def get(self, query):
        results = list(self.children(query))
        if len(results) != 1:
            raise ValueError(
                "{} children found matching query, "
                "expected 1".format(len(results))
            )
        return results[0]

    def get_with(self, query):
        results = list(self.children_with(query))
        if len(results) != 1:
            raise ValueError(
                "{} children found matching query, "
                "expected 1".format(len(results))
            )
        return results[0]

    def attach(self, node):
        """Add the given node as a child and update relevant indexes.

        This will detach the node from any parent it's currently attached to."""
        self._node_children.add(node)

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


def node_tree_summary(node, indent="    ", prefix=""):
    """Get a summary of all the the node tree starting from the given node."""
    name = "{} in {}".format(type(node).__name__, type(node).__module__)
    tree_string = prefix + name

    child_trees = Counter()
    for child in node.children(Node):
        subtree_string = node_tree_summary(child, prefix=(prefix + indent))
        child_trees[subtree_string] += 1

    for subtree_string, count in child_trees.most_common():
        indent_length = len(prefix + indent)

        subtree_string = "{}[{}] {}".format(
            subtree_string[:indent_length],
            count,
            subtree_string[indent_length:]
        )

        tree_string += "\n" + subtree_string
    return tree_string


# Functions that get called when a given object is found in a node's namespace
# {object: [functions_to_call]}
_on_instantiation = {}


def _get_instantiation_calls(cls):
    """Find attributes on the given class that are in on_instantiation."""
    calls = []
    for _, attr_value in getmembers(cls):
        try:
            calls.extend(_on_instantiation[attr_value])
        except (KeyError, TypeError):
            pass
    return calls


def add_instantiation_call(obj, func):
    """Add a function to called when a node is instantiated that contains the
    given object."""
    _on_instantiation.setdefault(obj, []).append(func)
