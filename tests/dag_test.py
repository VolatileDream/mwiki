import unittest
import sqlite3
from src.dag import DependencyGraph, NotFoundException

class DagTests(unittest.TestCase):
  def dag(self):
    return DependencyGraph(sqlite3.connect(":memory:",isolation_level=None))

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
