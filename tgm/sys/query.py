class Queryable:
    """Base class for a type which can be queried.

    Facilitates the use of the query language, e.g.
    Player["alive": true]
    """
    def __getitem__(self, item):
        """Provides the bracket notation on queryable classes allowing for
        shorthand query construction, e.g. Enemy["health": 0]
        """
        return Query(self).combine(_make_child_query(item))

    def __rshift__(self, rhs):
        """A special constraint, equivalent to the '>' constraint in CSS
        to select a direct descendent.

        e.g. Player >> Collider[Rect]
        which would select every collider that's attached to a Player and
        has a Rect attached to it.
        """
        rhs = make_query(rhs)
        lhs = make_query(self)
        return rhs.parent_matches(lhs)


class DummyQuery(Queryable):
    """Represents a query which does no filtering.  For internal use. """
    def _optimal_key(self, node):
        return object

    def combine(self, other):
        return other

    def test(self, node):
        return True


class Query(Queryable):
    """Set of conditions used to identify nodes in the scene graph."""
    def __init__(self,
                 key=object,
                 condition=lambda _: True,
                 parent_query=DummyQuery(),
                 child_query=DummyQuery(),
                 trim=lambda _: False):
        """Constructs a query object which can be used to find nodes in
        the scene graph.

        Specifying a key will limit results to only nodes which inherit
        that type.  The engine indexes objects by their types, making
        this the most performant (and concise) way to query for objects.
        """
        self._key = key
        self._condition = condition
        self._parent_query = parent_query
        self._child_query = child_query
        self._trim = trim

    def test(self, node):
        """Checks if the given node matches the query."""
        if not isinstance(node, self._key):
            return False

        if not self._condition(node):
            return False

        if self._trim(node):
            return False

        if not isinstance(self._child_query, DummyQuery):
            optimal_key = self._child_query._optimal_key(node)

            if not any(self._child_query.test(child)
                       for child in node._node_index[optimal_key]
                       if child is not node):
                return False

        if not isinstance(self._parent_query, DummyQuery):
            if not self._parent_query.test(node._node_parent):
                return False

        return True

    def find_in(self, node):
        """Return every descendent in the node which matches the query.

        When a node meets the trim condition, all of its descendents will
        be ignored.

        find_in returns a generator which is ideal for finding or iterating,
        but to get the full result set, convert it to a list, e.g.:
            list(query.find_in(world))
        """
        key = self._optimal_key(node)

        for child in node._node_index[key]:
            if child is node or self._trim(child):
                continue

            if self.test(child):
                yield child

            for nested_child in self.find_in(child):
                yield nested_child

    def find_on(self, node):
        """Return every direct descendent in the node which matches the query.

        Unlike find_in, find_on only returns descendents directly attached to
        the node: their children are not tested against.

        find_in returns a generator which is ideal for finding or iterating,
        but to get the full result set, convert it to a list, e.g.:
            list(query.find_in(world))
        """
        key = self._optimal_key(node)

        for child in node._node_index[key]:
            if child is node or self._trim(child):
                continue

            if self.test(child):
                yield child

    def filter(self, condition):
        """Adds a new condition to limit the results of a query
        e.g. Query(Player).filter(lambda player: player.health > 100)

        Returns a new Query object, rather than modifying the existing one.
        """
        return self.combine(Query(condition=condition))

    def trim(self, condition):
        """Filter out a node and all descendents it matches.

        e.g. Query(Node).trim(Disabled)

        Returns a new Query object, rather than modifying the existing one.
        """
        return self.combine(Query(trim=condition))

    def child_matches(self, child_query):
        """Query that any of the node's direct descendents must match.

        e.g. Query(Node).child_matches(Query(Collider))
        which would select every node which has a collider.

        Returns a new Query object.
        """
        return self.combine(Query(child_query=child_query))

    def parent_matches(self, parent_query):
        """Query that the node's parent must match.

        e.g. Query(Collider).parent_matches(Query(Enemy))
        which would select every collider attached to an enemy.

        Returns a new Query object.
        """
        return self.combine(Query(parent_query=parent_query))

    def combine(self, other):
        """Join two queries together.  The result of combine is a query that
        returns results that match both queries.

        This only merges the conditions of the queries together.  The query
        will not be performed until test, find_in or find_all are called.

        Combine is the primary means of composing queries, and it is the case
        which will generate the most optimal queries.  Query construction can
        be expensive to perform in every step, thus for complicated queries it
        may be preferable to construct the query during initialization and then
        reuse that query every step.

        Returns a new Query object, instead of mutating the old one.
        """
        if isinstance(other, DummyQuery):
            return self

        child_query = self._child_query.combine(other._child_query)
        parent_query = self._parent_query.combine(other._parent_query)

        def condition(node):
            return self._condition(node) and other._condition(node)

        def trim(node):
            return self._trim(node) or other._trim(node)

        # Pick the most specific key
        if issubclass(other._key, self._key):
            key = other._key
        elif issubclass(self._key, other._key):
            key = self._key
        else:
            # If neither key is a superclass of the other
            # pick one key and add the other as a condition
            key = self._key
            old_condition = condition

            def condition(node):
                return old_condition(node) and isinstance(node, other._key)

        return Query(key, condition, parent_query, child_query, trim)

    def _optimal_key(self, node):
        """Find the key which requires testing the minimal number of nodes."""
        optimal_key = self._child_query._optimal_key(node)

        key_count = len(node._node_index[self._key])
        optimal_key_count = len(node._node_index[optimal_key])

        if key_count < optimal_key_count:
            return self._key
        return optimal_key


def make_query(item):
    """Constructs a Query from a Queryable."""
    if isinstance(item, Query):
        return item
    return Query(item)


def _query_slice(item):
    """Create a Query from a slice, used by _make_child_query"""
    attr, value = item.start, item.stop
    return Query(
        condition=lambda x: hasattr(x, attr) and getattr(x, attr) == value
    )


def _query_tuple(item):
    """Create a Query from a tuple, used by _make_child_query"""
    query = Query()
    for child in item:
        query = query.combine(_make_child_query(child))
    return query


# Functions used to construct a child query for a given input type
_child_query_cases = {
    Query: lambda item: Query(child_query=item),
    slice: _query_slice,
    tuple: _query_tuple,
    str: lambda item: Query(condition=lambda x: hasattr(x, item))
}


def _make_child_query(item):
    """Make a Query to limit child nodes, used by Queryable.__getitem__."""
    try:
        return _child_query_cases[type(item)](item)
    except KeyError:
        pass

    # special fallback check for where item has a metaclass
    if isinstance(item, type):
        _child_query_cases[type(item)] = lambda item: Query(
            child_query=Query(item)
        )
        return _child_query_cases[type(item)](item)

    if callable(item):
        return Query(condition=item)

    raise TypeError(
        "invalid object '{}' in query.".format(item)
    )
