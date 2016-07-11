from collections import defaultdict, Counter
from inspect import getmro, getmembers
from tgm.sys import Queryable, Query, make_query
from itertools import chain


class NodeMeta(Queryable, type):
    """The metaclass which makes Node subclasses into Queryable instances."""
    pass


class Node(metaclass=NodeMeta):
    """The base class for all objects in the scene graph."""
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)

        # The attributes representing the node's position on the scene
        obj._node_parent = None
        obj._node_children = defaultdict(set)

        # Maps types to child nodes which are of given type or have a
        # descendent of given type.  If self is of this type, it is included
        obj._node_index = defaultdict(set)

        # Register each base class in the index of the created object
        for key in getmro(type(obj)):
            obj._add_index_key(key, obj)

        for call in _get_instantiation_calls(cls):
            call(obj)

        return obj

    def attach(self, node):
        """Add the given node as a child.

        Detaches the node from any parent it's currently attached to.

        >>> world.attach(Player("bob"))
        <mygame.player.Player at 318f9f0>
        """
        for key in getmro(type(node)):
            self._node_children[key].add(node)

        if node.parent() is not None:
            node.parent()._detach(node)

        node._node_parent = self
        for key, node_set in node._node_index.items():
            if node_set:
                self._add_index_key(key, node)

        return node

    def destroy(self):
        """Destroy the object and all its descendants from the game.

        Recursively destroys each child node then destroys the object.

        >>> player.destroy()
        None
        """
        for child in self.children(Node):
            child.destroy()

        if self.parent() is not None:
            self.parent()._detach(self)

    def parent(self, query=None):
        """Return the first parent that satisfies the query, starting with the
        direct parent.

        If no query is given then the object's direct parent will be returned.

        >>> self.parent(World)
        <tgm.game.world.World at 329f8f0>
        """
        if query is None or query is Node:
            return self._node_parent

        if isinstance(query, Query):
            test = query.test
        else:
            def test(node):
                return isinstance(node, query)

        parent = self._node_parent
        while parent is not None:
            if test(parent):
                return parent
            parent = parent._node_parent

        raise ValueError("No parent found matching the given query")

    def children(self, query):
        """Return immediate children which match the query.

        >>> list(world.children(Entity))
        [<mygame.player.Player at 318f9f0>, <mygame.enemy.Enemy at 319f9f0>]
        """
        if not isinstance(query, Query):
            return iter(self._node_children[query])

        return query.find_on(self)

    def get(self, query):
        """Return the child that matches the query.

        Expects only one child to match the query.

        TODO: example
        """
        if isinstance(query, Query):
            results = tuple(self.children(query))
        else:
            results = tuple(self._node_children[query])
        assert len(results) == 1, (
            "{} children found matching query, expected 1".format(len(results))
        )
        return results[0]

    def find(self, query, trim=None):
        """Return all children, their children, etc. which match the query.

        If a node matches the trim condition (function or query), the node
        and all of its descendents will be ignored.

        >>> world.find(Enemy)
        [<mygame.enemy.Enemy at 318f9f0>, <mygame.enemy.Enemy at 318e9f0>]
        """
        if trim is None:
            if not isinstance(query, Query):
                return (candidate
                        for child in self._node_index[query]
                        if child is not self
                        for candidate in _find_fast(child, query))
        else:
            if isinstance(trim, Queryable):
                trim = make_query(trim).test

            if not isinstance(query, Query):
                return chain.from_iterable(
                    _find_fast_trim(child, query, trim)
                    for child in self._node_index[query]
                    if child is not self
                )

            query = query.trim(trim)

        return query.find_in(self)

    def children_with(self, query):
        """Return immediate children which have a child matching the query.

        >>> layer.children_with(Collider)
        [<mygame.player.Player at 318f9f0>, <mygame.enemy.Enemy at 319f9f0>]
        """
        if not isinstance(query, Query):
            return (child
                    for child in self._node_index[query]
                    if child is not self and child._node_children[query])

        return Query(Node).child_matches(query).find_on(self)

    def get_with(self, query):
        """Return the child which has a child matching a given query."""
        if isinstance(query, Query):
            results = tuple(self.children_with(query))
        else:
            results = [child
                       for child in self._node_index[query]
                       if child is not self and child._node_children[query]]
        assert len(results) == 1, (
            "{} children found matching query, expected 1".format(len(results))
        )
        return results[0]

    def find_with(self, query, trim=None):
        """Find descendents which have a child matching the query.

        If a node matches the trim condition (function or query), the node
        and all of its descendents will be ignored.

        >>> world.find_with(Collider)
        [<mygame.enemy.Enemy at 318f9f0>, <mygame.player.Player at 318e9f0>]
        """
        if trim is None:
            if not isinstance(query, Query):
                return _find_with_fast(self, query)
            full_query = Query(Node, child_query=query)
        else:
            if isinstance(trim, Queryable):
                trim = make_query(trim).test

            if not isinstance(query, Query):
                return _find_with_fast_trim(self, query, trim)

            full_query = Query(Node, trim=trim, child_query=query)

        return full_query.find_in(self)

    def matches(self, query):
        """Return if the node matches the given query.

        >>> player.match(Player)
        True
        >>> player.match(Player["health", lambda player: player.health > 0])
        True
        """
        return make_query(query).test(self)

    def _detach(self, node):
        """Detach the given node from its parent."""
        for key, node_set in node._node_index.items():
            if node_set:
                self._remove_index_key(key, node)

        for key in getmro(type(node)):
            self._node_children[key].remove(node)
        node._node_parent = None

        return node

    def _add_index_key(self, key, node):
        """Register this object as having a given key."""
        if (self.parent() is not None) and (not self._node_index[key]):
            self.parent()._add_index_key(key, self)

        self._node_index[key].add(node)

    def _remove_index_key(self, key, node):
        """Unregister this object as having a given key."""
        self._node_index[key].remove(node)

        if (self.parent() is not None) and (not self._node_index[key]):
            self.parent()._remove_index_key(key, self)

    def __repr__(self):
        return "<{module}.{type} at {id:x}>".format(
            type=type(self).__name__,
            module=type(self).__module__,
            id=id(self)
        )


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


def _find_fast(node, key):
    """Optimised version of Node's find for a simple key and no trim.

    Unlike Node's find, this function can return the node passed in if
    it matches. As such to get the same behaviour is should be called
    on each child."""
    for child in node._node_index[key]:
        if child is node:
            yield child
            continue

        for nested_child in _find_fast(child, key):
            yield nested_child


def _find_fast_trim(node, key, trim):
    """Optimised version of Node's find for a simple key and a trim function.

    Unlike Node's find, this function can return the node passed in if
    it matches. As such to get the same behaviour is should be called
    on each child."""
    for child in node._node_index[key]:
        if trim(child):
            continue

        if child is node:
            yield child
            continue

        for nested_child in _find_fast_trim(child, key, trim):
            yield nested_child


def _find_with_fast(node, key):
    """Optimised version of Node's find_with for a simple key and no trim."""
    for child in node._node_index[key]:
        if child is node:
            continue

        if child._node_children[key]:
            yield child

        for nested_child in _find_with_fast(child, key):
            yield nested_child


def _find_with_fast_trim(node, key, trim):
    """Optimised version of Node's find_with for a simple key and a trim."""
    for child in node._node_index[key]:
        if child is node or trim(child):
            continue

        if child._node_children[key]:
            yield child

        for nested_child in _find_with_fast_trim(child, key, trim):
            yield nested_child


# Functions that get called when a given object is found in a node's namespace
# {object: [functions_to_call]}
_on_instantiation = {}


def _get_instantiation_calls(cls):
    """Find every on_instantiation call associated with an attribute on the
    given class."""
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
