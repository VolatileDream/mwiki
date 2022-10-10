import unittest
import sqlite3
from pymwiki.dag import DependencyGraph
from pymwiki.exceptions import NotFoundException

class DagTests(unittest.TestCase):
  def dag(self):
    return DependencyGraph.open(":memory:")

  def test_add_build(self):
    d = self.dag()

    d.add("abc")
    self.assertEqual(d.status("abc").value, 2)

    l = list(d.rebuild_instructions("abc"))
    self.assertEqual(l, ["abc"])

  def test_missing_item(self):
    d = self.dag()

    with self.assertRaises(NotFoundException):
      d.edge("abc", "def")

  def test_add_edge(self):
    d = self.dag()

    d.add("a")
    d.add("b")

    for n in d.rebuild_instructions():
      d.mark_rebuilt(n)

    d.edge("a", "b")

    self.assertEqual(d.status("a").value, 1)
    self.assertEqual(d.status("b").value, 2)

  def test_remove_edge(self):
    d = self.dag()

    d.add("a")
    d.add("b")
    d.add("c")
    d.edge("a", "b")
    d.edge("b", "c")

    for n in d.rebuild_instructions():
      d.mark_rebuilt(n)

    deps, rdeps = d.remove("b")
    self.assertEqual(deps, ["a"])
    self.assertEqual(rdeps, ["c"])

    self.assertEqual(d.status("c"), 2)

    with self.assertRaises(NotFoundException):
      d.status("b")

  def test_changed(self):
    d = self.dag()

    d.add("a")
    d.add("b")

    self.assertEqual(d.changed(), set(["a", "b"]))

  def test_building(self):
    d = self.dag()

    d.add("abc")
    d.add("def")
    d.edge("abc", "def")

    with self.assertRaises(Exception):
      d.mark_rebuilt("def")

    d.mark_rebuilt("abc")
    d.mark_rebuilt("def")

    d.mark_changed("abc")
    l = list(d.rebuild_instructions())
    self.assertEqual(l, ["abc", "def"])

    d.mark_rebuilt("abc")
    l = list(d.rebuild_instructions())
    self.assertEqual(l, ["def"])

  def test_build_cycle(self):
    d = self.dag()

    d.add("abc")
    d.add("def")
    d.edge("abc", "def")
    with self.assertRaises(Exception):
      d.edge("def", "abc")

  def test_build_order(self):
    d = self.dag()

    d.add("a")
    d.add("b")
    d.add("c")
    d.add("d")
    d.add("e")
    d.add("f")
    d.add("g")

    d.edge("a", "b")
    d.edge("a", "c")
    d.edge("b", "c")

    d.edge("c", "d")
    d.edge("c", "e")
    d.edge("c", "f")

    l = list(d.rebuild_instructions("c"))
    self.assertEqual(l, ["a", "b", "c"])

    d.mark_rebuilt("a")
    d.mark_rebuilt("b")
    d.mark_rebuilt("c")

    l = list(d.rebuild_instructions("d"))
    self.assertEqual(l, ["d"])
  
    # Because none of these have dependencies. 
    l = set(d.rebuild_instructions())
    self.assertSetEqual(l, set(["d", "e", "f", "g"]))

  def test_check_dependencies(self):
    d = self.dag()

    d.add("a")
    d.add("b")
    d.add("c")

    d.edge("a", "b")
    d.edge("b", "c")

    self.assertFalse(d.has_dependencies("a"))
    self.assertTrue(d.has_dependencies("b"))
    self.assertTrue(d.has_dependencies("c"))

    self.assertEqual(d.dependencies("a"), set([]))
    self.assertEqual(d.dependencies("b"), set(["a"]))
    self.assertEqual(d.dependencies("c"), set(["b"]))

    self.assertEqual(d.dependencies("a", deps_of_deps=True), set([]))
    self.assertEqual(d.dependencies("b", deps_of_deps=True), set(["a"]))
    self.assertEqual(d.dependencies("c", deps_of_deps=True), set(["b", "a"]))

    d.add("d")
    d.add("e")
    d.edge("c", "d")
    d.edge("d", "e")

    self.assertEqual(d.dependencies("d", deps_of_deps=True), set(["b", "c"]))
    self.assertEqual(d.dependencies("e", deps_of_deps=True), set(["c", "d"]))

  def test_iterate(self):
    # Needed because iterating storage isn't guaranteed to work.
    # There's no guarantee a key exists in storage, but it _is_ guaranteed
    # to always exist in the DependencyGraph.

    d = self.dag()

    d.add("a1")
    d.add("a2")
    d.add("a3")
    d.add("b1")
    d.add("b2")
    d.add("c1")

    self.assertEqual(set(d.iterate(prefix="a")), set(["a1", "a2", "a3"]))
