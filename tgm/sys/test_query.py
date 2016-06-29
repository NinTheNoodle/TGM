from unittest import TestCase
from unittest.mock import Mock
from tgm.sys import Node
from .query import Queryable, DummyQuery, Query
# from pdb import set_trace


class DummyNode(Node):
    pass


class DummyNode2(Node):
    pass


class DummyNode3(DummyNode, DummyNode2):
    pass


class TestQueryable(TestCase):
    def test_getitem(self):
        query = DummyNode2[DummyNode]

        self.assertIs(query._key, DummyNode2)
        self.assertIs(query._child_query._key, DummyNode)

    def test_rshift(self):
        query = DummyNode >> DummyNode2

        self.assertIs(query._key, DummyNode2)
        self.assertIs(query._parent_query._key, DummyNode)


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
    def test_combine(self):
        # combining a real query with a dummy query
        query = Query()
        self.assertIs(query.combine(DummyQuery()), query)
        self.assertIs(DummyQuery().combine(query), query)

        # picks optimal key
        self.assertIs(Query(Node).combine(Query(DummyNode))._key, DummyNode)

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
        query = Query(DummyNode).combine(Query(DummyNode2))
        # one sibling is not being checked by the query
        self.assertTrue(
            query._condition(DummyNode()) ^ query._condition(DummyNode2())
        )
        # DummyNode3 is both a DummyNode and a DummyNode2
        self.assertTrue(query._condition(DummyNode3()))

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
