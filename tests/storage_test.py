import unittest
import sqlite3
from pymwiki.storage import Storage
from pymwiki.exceptions import NotFoundException

class StorageTests(unittest.TestCase):
  def store(self):
    return Storage.open(":memory:")

  def test_add_build(self):
    s = self.store()

    s.put("abc", "def")
    self.assertEqual(s.get("abc"), "def")

    self.assertTrue(s.contains("abc"))

    l = list(s.iterate())
    self.assertEqual(l, ["abc"])

  def test_missing_item(self):
    s = self.store()

    self.assertFalse(s.contains("abc"))

    with self.assertRaises(NotFoundException):
      s.get("abc")

    self.assertEqual(s.get("abc", None), None)
    self.assertEqual(s.get("abc", "def"), "def")

    s.remove("abc")

  def test_update(self):
    s = self.store()

    s.put("abc", "def")
    self.assertEqual(s.get("abc"), "def")

    s.put("abc", "ghi")

    self.assertEqual(s.get("abc"), "ghi")

  def test_add_remove(self):
    s = self.store()

    s.put("abc", "def")
    self.assertEqual(s.get("abc"), "def")

    s.put("abc", "ghi")

    self.assertEqual(s.get("abc"), "ghi")

  def test_iterate(self):
    s = self.store()

    s.put("a1", " a1")
    s.put("a2", " a2")
    s.put("a3", " a3")
    s.put("a4", " a4")
    s.put("a5", " a5")

    s.put("b1", " b1")

    l = list(s.iterate(prefix="a"))
    self.assertEqual(l, ["a1", "a2", "a3", "a4", "a5"])
