from unittest import TestCase
from tgm.sys.node import _get_instantiation_calls, _on_instantiation
from tgm.sys import Node, Query, add_instantiation_call
from inspect import getmro
from unittest.mock import patch, Mock


class TestNode(TestCase):
    def test_init(self):
        # check that all the base classes have been added as keys
        with patch("tgm.sys.node.Node._add_index_key") as mock:
            node = Node()
            for key in getmro(type(node)):
                mock.assert_any_call(key, node)

        # check that everything in _get_instantiation_calls calls get called
        call_mocks = [Mock(), Mock()]
        with patch("tgm.sys.node._get_instantiation_calls",
                   lambda _: call_mocks):
            node = Node()
            for mock in call_mocks:
                mock.assert_called_once_with(node)

    def test_attach(self):
        parent = Node()
        child = parent.attach(Node())

        # check for the parent being set
        self.assertIs(child._node_parent, parent)

        # check for the child being in the relevant direct child sets
        for key in getmro(type(child)):
            self.assertIn(child, parent._node_children[key])

        # check that _detach is called if the node already had a parent
        new_parent = Node()
        with patch("tgm.sys.node.Node._detach") as mock:
            new_parent.attach(child)
            mock.assert_called_once_with(child)
        self.assertIs(child._node_parent, new_parent)

        # check for _add_index_key being called for everything in the
        # child's index
        parent = Node()
        child = Node()
        with patch("tgm.sys.node.Node._add_index_key") as mock:
            parent.attach(child)
            for key, node_set in child._node_index.items():
                if node_set:
                    mock.assert_any_call(key, child)

        # the return value should be the child
        parent = Node()
        child = Node()
        self.assertIs(parent.attach(child), child)

    def test_destroy(self):
        # check that all every child has destroy called
        node = Node()
        children_mocks = [Mock(), Mock()]
        with patch("tgm.sys.node.Node.children", lambda _, _2: children_mocks):
            node.destroy()
            for mock in children_mocks:
                mock.destroy.assert_called_once_with()

        # check that the parent's _detach has been called
        parent = Node()
        child = parent.attach(Node())
        with patch("tgm.sys.node.Node._detach") as mock:
            child.destroy()
            mock.assert_called_once_with(child)

    def test_parent(self):
        # get direct parent
        parent = Node()
        child = parent.attach(Node())
        self.assertIs(child.parent(), parent)
        self.assertIs(child.parent(Node), parent)

        # get specific parent full query
        class Level(Node):
            pass

        game = Node()
        level = game.attach(Level())
        layer = level.attach(Node())
        player = layer.attach(Node())

        with patch("tgm.sys.query.Query.test",
                   lambda _, obj: isinstance(obj, Level)):
            self.assertIs(player.parent(Query()), level)

        # get specific parent key only
        self.assertIs(player.parent(Level), level)

        # check no valid parent
        with patch("tgm.sys.query.Query.test", lambda _, obj: False):
            with self.assertRaises(ValueError):
                player.parent(Query())

    def test_children(self):
        node = Node()

        # check finding a child
        child = node.attach(Node())
        self.assertEqual(list(node.children(Node)), [child])

        # check full query call
        with patch("tgm.sys.query.Query.find_on") as mock:
            node.children(Query())
            mock.assert_called_once_with(node)

    def test_get(self):
        # check that the child is returned
        parent = Node()
        child = parent.attach(Node())
        self.assertIs(parent.get(Node), child)

    def test_find(self):
        node = Node()
        with patch("tgm.sys.query.Query.find_in") as mock:
            # check call with query
            node.find(Query())
            mock.assert_called_once_with(node)

            # check call with key
            mock.reset_mock()
            node.find(Node)
            mock.assert_called_once_with(node)

        # check trimming full query
        def trim(_):
            return False

        with patch("tgm.sys.query.Query.trim") as mock:
            node.find(Query(), trim=trim)
            mock.assert_called_once_with(trim)

        # check trimming key only
        query_mock = Mock()

        # for allowing isinstance(..., Query) to work
        class QueryMock(Query):
            def __new__(cls, *args, **kwargs):
                return query_mock(*args, **kwargs)

        with patch("tgm.sys.node.Query", QueryMock):
            node.find(Node, trim=trim)
            query_mock.assert_called_once_with(Node, trim=trim)

    def test_children_with(self):
        node = Node()

        # check finding a child
        child = node.attach(Node())
        child.attach(Node())
        self.assertEqual(list(node.children_with(Node)), [child])

        # check full query call
        with patch("tgm.sys.query.Query.find_on") as mock:
            node.children(Query())
            mock.assert_called_once_with(node)

    def test_get_with(self):
        # check that the child is returned
        parent = Node()
        child = parent.attach(Node())
        child.attach(Node())
        self.assertIs(parent.get_with(Node), child)

    def test_find_with(self):
        node = Node()
        with patch("tgm.sys.query.Query.find_in") as mock:
            # check call with query
            node.find_with(Query())
            mock.assert_called_once_with(node)

            # check call with key
            mock.reset_mock()
            node.find_with(Node)
            mock.assert_called_once_with(node)

    def test_matches(self):
        node = Node()
        with patch("tgm.sys.query.Query.test") as mock:
            node.matches(Query())
            mock.assert_called_once_with(node)

    def test_detach(self):
        parent = Node()
        child = parent.attach(Node())
        parent._detach(child)

        # check for the child being removed from the relevant direct child sets
        for key in getmro(type(child)):
            self.assertNotIn(child, parent._node_children[key])

        # check for _remove_index_key being called for everything in the
        # child's index
        parent = Node()
        child = parent.attach(Node())
        with patch("tgm.sys.node.Node._remove_index_key") as mock:
            parent._detach(child)
            for key, node_set in child._node_index.items():
                if node_set:
                    mock.assert_any_call(key, child)

    def test_add_index_key(self):
        class Key:
            pass

        world = Node()
        level = world.attach(Node())
        player = level.attach(Node())
        enemy = level.attach(Node())

        # check single child with key
        player._add_index_key(Key, player)
        self.assertEqual(enemy._node_index[Key], set())
        self.assertEqual(player._node_index[Key], {player})
        self.assertEqual(level._node_index[Key], {player})
        self.assertEqual(world._node_index[Key], {level})

        # check two children with key
        enemy._add_index_key(Key, enemy)
        self.assertEqual(enemy._node_index[Key], {enemy})
        self.assertEqual(player._node_index[Key], {player})
        self.assertEqual(level._node_index[Key], {player, enemy})
        self.assertEqual(world._node_index[Key], {level})

    def test_remove_index_key(self):
        class Key:
            pass

        world = Node()
        level = world.attach(Node())

        player = level.attach(Node())
        enemy = level.attach(Node())

        player._add_index_key(Key, player)
        enemy._add_index_key(Key, enemy)
        world._add_index_key(Key, world)

        # check remove key with sibling having key
        # index removal should stop at the immediate parent
        player._remove_index_key(Key, player)
        self.assertEqual(enemy._node_index[Key], {enemy})
        self.assertEqual(player._node_index[Key], set())
        self.assertEqual(level._node_index[Key], {enemy})
        self.assertEqual(world._node_index[Key], {level, world})

        # check removing key propagation
        # world has the key directly, so it should remain
        enemy._remove_index_key(Key, enemy)
        self.assertEqual(enemy._node_index[Key], set())
        self.assertEqual(player._node_index[Key], set())
        self.assertEqual(level._node_index[Key], set())
        self.assertEqual(world._node_index[Key], {world})

        # ensure that removing the key from world works too
        world._remove_index_key(Key, world)
        self.assertEqual(world._node_index[Key], set())


class TestOnInstantiationCalls(TestCase):
    def test_add_instantiation_call(self):
        key = object()

        def call1(node):
            pass

        def call2(node):
            pass

        # check that the key does not exist yet
        self.assertNotIn(key, _on_instantiation)

        # check adding a single instantiation call
        add_instantiation_call(key, call1)
        self.assertEqual(_on_instantiation[key], [call1])

        # check adding a second instantiation call
        add_instantiation_call(key, call2)
        self.assertEqual(_on_instantiation[key], [call1, call2])

    def test_get_instantiation_calls(self):
        key1, call1 = object(), lambda _: None
        key2, call2 = object(), lambda _: None
        key3, call3 = object(), lambda _: None
        key4, call4 = object(), lambda _: None

        add_instantiation_call(key1, call1)
        add_instantiation_call(key2, call2)
        add_instantiation_call(key3, call3)
        add_instantiation_call(key4, call4)

        class Base(Node):
            a = key1
            b = key2

        class Player(Base):
            c = key3
            a = key4
            z = "unrelated"

        # should find the instantiation calls for the a,b and c attributes
        # key4 should shadow key1, so key1 should not be called
        self.assertEqual(set(_get_instantiation_calls(Player)),
                         {call2, call3, call4})
