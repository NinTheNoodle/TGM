def matches_key(node, key):
    return node in node._node_index[key]


def join_tests(a, b):
    return lambda node: a(node) and b(node)


class Query:
    def __init__(self,
                 key,
                 test=lambda _: True,
                 stop_at=lambda _: False,
                 subqueries=tuple()):
        self.key = key
        self.test = test
        self.stop_at = stop_at
        self.subqueries = subqueries

    def filter(self, new_test):
        return Query(self.key, join_tests(self.test, new_test),
                     subqueries=self.subqueries)

    def with_child(self, query):
        def filter_by_child(node):
            return any(query.matches(child)
                       for child in node._node_index[query.key]
                       if child is not node)

        subqueries = self.subqueries + (query,)

        return (Query(self.key, self.test, subqueries=subqueries)
                .filter(filter_by_child))

    def matches(self, node):
        return matches_key(node, self.key) and self.test(node)

    def keys(self):
        yield self.key
        for query in self.subqueries:
            for key in query.keys():
                yield key

    def optimal_key(self, node):
        optimal = self.key
        optimal_count = len(node._node_index[self.key])
        for key in self.keys():
            count = len(node._node_index[key])
            if count < optimal_count:
                optimal = key
                optimal_count = count

        return optimal, optimal_count

    def find_in(self, node):
        key, _ = self.optimal_key(node)

        for child in node._node_index[key]:
            if not self.stop_at(child):
                if child is node:
                    continue

                if matches_key(child, self.key) and self.test(child):
                    yield child

                for nested_child in self.find_in(child):
                    yield nested_child

    def find_on(self, node):
        for child in node._node_index[self.key]:
            if not self.stop_at(child):
                if child is node:
                    continue

                if matches_key(child, self.key) and self.test(child):
                    yield child

    # TODO: __repr__ and refactor
