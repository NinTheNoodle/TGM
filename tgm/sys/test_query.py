from unittest import TestCase
from unittest.mock import patch, Mock
from tgm.sys import Node
from tgm.sys.query import (
    DummyQuery, Query, make_query, _query_slice, _query_tuple,
    _make_child_query, _child_query_cases
)
# from pdb import set_trace


class DummyNodeA(Node):
    pass


class DummyNodeB(Node):
    pass


class DummyNodeAB(DummyNodeA, DummyNodeB):
    pass


class TestQueryable(TestCase):
    def test_getitem(self):
        query = DummyNodeB[DummyNodeA]

        self.assertIs(query._key, DummyNodeB)
        self.assertIs(query._child_query._key, DummyNodeA)

    def test_rshift(self):
        query = DummyNodeA >> DummyNodeB

        self.assertIs(query._key, DummyNodeB)
        self.assertIs(query._parent_query._key, DummyNodeA)


class TestDummyQuery(TestCase):
    def test_optimal_key(self):
        self.assertIs(DummyQuery()._optimal_key(Node()), object)

    def test_combine(self):
        self.assertIsInstance(
            DummyQuery().combine(DummyQuery()),
            DummyQuery
        )

    def test_test(self):
        self.assertTrue(DummyQuery().test(Node()))


class TestQuery(TestCase):
    def test_test(self):
        world = Node()
        for i in range(10):
            world.attach(DummyNodeA())

            b = DummyNodeB()
            b.furious = True
            world.attach(b)

        # test for key
        self.assertEqual(10, len(list(Query(DummyNodeA).find_on(world))))

        # test for condition
        query = Query(Node).filter(
            lambda node: not isinstance(node, DummyNodeB)
        )
        self.assertEqual(10, len(list(query.find_on(world))))

        # test for trim
        query = Query(Node).filter(lambda node: not node.furious)

    def test_find_in(self):
        world = Node()
        for i in range(10):
            world.attach(DummyNodeA())

        # test basic find by key
        results = list(Query(Node).find_in(world))
        self.assertEqual(10, len(results))

        # test nested selection
        for i, node in enumerate(results):
            node.attach(DummyNodeB())
            node.angry = (i % 2) == 0
        results = list(Query(Node).find_in(world))
        self.assertEqual(20, len(results))

        # test trim
        query = Query(Node).trim(
            lambda node: hasattr(node, "angry") and node.angry
        )
        results = list(query.find_in(world))
        self.assertEqual(10, len(results))

    def test_find_on(self):
        world = Node()
        for i in range(10):
            world.attach(DummyNodeA())

        # test basic find by key
        results = list(Query(Node).find_on(world))
        self.assertEqual(10, len(results))

        # ensure non-nested selection
        for i, node in enumerate(results):
            node.attach(DummyNodeB())
            node.angry = (i % 2) == 0
        results = list(Query(Node).find_on(world))
        self.assertEqual(10, len(results))

    def test_filter(self):
        query = Query().filter(lambda x: x == "gnah")
        self.assertTrue(query._condition("gnah"))

    def test_trim(self):
        query = Query().trim(lambda x: x == "gnah")
        self.assertTrue(query._trim("gnah"))

    def test_child_matches(self):
        with patch('tgm.sys.query.Query.combine') as mock:
            Query().child_matches(Query())
            self.assertTrue(mock.called)

    def test_parent_matches(self):
        with patch('tgm.sys.query.Query.combine') as mock:
            Query().parent_matches(Query())
            self.assertTrue(mock.called)

    def test_combine(self):
        # combining a real query with a dummy query
        query = Query()
        self.assertIs(query.combine(DummyQuery()), query)
        self.assertIs(DummyQuery().combine(query), query)

        # picks optimal key
        self.assertIs(Query(Node).combine(Query(DummyNodeA))._key, DummyNodeA)

        # combines conditions
        true_query = Query(condition=lambda _: True)
        false_query = Query(condition=lambda _: False)
        query1 = true_query.combine(false_query)
        query2 = false_query.combine(true_query)
        self.assertFalse(query1._condition(Node()))
        self.assertFalse(query2._condition(Node()))

        # combines trim conditions
        query1 = (Query(trim=lambda _: True)
                  .combine(Query(trim=lambda _: False)))
        query2 = (Query(trim=lambda _: False)
                  .combine(Query(trim=lambda _: False)))
        self.assertTrue(query1._trim(Node()))
        self.assertFalse(query2._trim(Node()))

        # combines sibling query by adding a condition
        query = Query(DummyNodeA).combine(Query(DummyNodeB))
        # one sibling is not being checked by the query
        self.assertTrue(
            query._condition(DummyNodeA()) ^ query._condition(DummyNodeB())
        )
        # DummyNodeAB is both a DummyNodeA and a DummyNodeB
        self.assertTrue(query._condition(DummyNodeAB()))

        # ensure child and parent queries are combined
        def keyed_mock():
            return Mock(_key=object)

        query1 = Query(child_query=keyed_mock(), parent_query=keyed_mock())
        query2 = Query(child_query=keyed_mock(), parent_query=keyed_mock())
        query1.combine(query2)
        query1._parent_query.combine.assert_called_once_with(
            query2._parent_query
        )
        query1._child_query.combine.assert_called_once_with(
            query2._child_query
        )

    def test_optimal_key(self):
        world = Node()
        for i in range(10):
            node = DummyNodeA()
            if (i % 2) == 0:
                node.attach(DummyNodeB())
            world.attach(node)

        query = Query(DummyNodeA).child_matches(Query(DummyNodeB))
        self.assertEqual(DummyNodeB, query._optimal_key(world))


class TestQueryUtilities(TestCase):
    def test_make_query(self):
        self.assertIs(Query, type(make_query(Node)))
        self.assertIs(Query, type(make_query(Query())))

    def test_query_slice(self):
        query = _query_slice(slice("hates_life", True))
        node = Node()
        node.hates_life = True
        self.assertTrue(query.test(node))

    def test_query_tuple(self):
        items = (Node, lambda x: x == "geh")
        query = _query_tuple(items)
        self.assertIs(Node, query._child_query._key)
        self.assertTrue(query._child_query._condition("geh"))

    @patch('tgm.sys.query._child_query_cases', wraps=_child_query_cases)
    def test_make_child_query(self, cases_mock):
        _make_child_query(Query())
        cases_mock.__getitem__.assert_called_once_with(Query)
        cases_mock.reset_mock()

        _make_child_query(slice("yes", "no"))
        cases_mock.__getitem__.assert_called_once_with(slice)
        cases_mock.reset_mock()

        _make_child_query(tuple())
        cases_mock.__getitem__.assert_called_once_with(tuple)
        cases_mock.reset_mock()

        _make_child_query("tagme")
        cases_mock.__getitem__.assert_called_once_with(str)
        cases_mock.reset_mock()
