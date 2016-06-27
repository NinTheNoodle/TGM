class DummyQuery:
    def optimal_key(self, node):
        return object

    def combine(self, other):
        return other

    def test(self, node):
        return True


class Query:
    def __init__(self,
                 key=object,
                 condition=lambda _: True,
                 parent_query=DummyQuery(),
                 child_query=DummyQuery(),
                 trim=lambda _: False):
        self.key = key
        self.condition = condition
        self.parent_query = parent_query
        self.child_query = child_query
        self.trim = trim

    def child_matches(self, child_query):
        return self.combine(Query(child_query=child_query))

    def parent_matches(self, parent_query):
        return self.combine(Query(parent_query=parent_query))

    def filter(self, condition):
        return self.combine(Query(condition=condition))

    def combine(self, other):
        if isinstance(other, DummyQuery):
            return self

        child_query = self.child_query.combine(other.child_query)
        parent_query = self.parent_query.combine(other.parent_query)

        condition = lambda node: (self.condition(node) and
                                  other.condition(node))

        # Pick the most specific key
        if issubclass(other.key, self.key):
            key = other.key
        elif issubclass(self.key, other.key):
            key = self.key
        else:
            # If neither key is a superclass of the other
            # pick one key and add the other as a condition
            key = self.key
            condition = lambda node: (condition(node) and
                                      isinstance(node, other.key))

        return Query(key, condition, parent_query, child_query)

    def optimal_key(self, node):
        optimal_key = self.child_query.optimal_key(node)
        if len(node._node_index[self.key]) < len(node._node_index[optimal_key]):
            return self.key
        return optimal_key

    def find_in(self, node):
        key = self.optimal_key(node)

        for child in node._node_index[key]:
            if child is node or self.trim(child):
                continue

            if self.test(child):
                yield child

            for nested_child in self.find_in(child):
                yield nested_child

    def find_on(self, node):
        key = self.optimal_key(node)

        for child in node._node_index[key]:
            if child is node or self.trim(child):
                continue

            if self.test(child):
                yield child

    def test(self, node):
        if not isinstance(node, self.key):
            return False

        if not isinstance(self.child_query, DummyQuery):
            optimal_key = self.child_query.optimal_key(node)

            if not any(self.child_query.test(child)
                       for child in node._node_index[optimal_key]
                       if child is not node):
                return False

        if not isinstance(self.parent_query, DummyQuery):
            if not self.parent_query.test(node._node_parent):
                return False

        return True
