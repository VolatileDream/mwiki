import unittest
import sqlite3
from src.storage import Storage
from src.exceptions import NotFoundException

class StorageTests(unittest.TestCase):
  def store(self):
    return Storage.open(":memory:")

  def test_add_build(self):
    s = self.store()

    s.add("abc", "def")
    self.assertEqual(s.get("abc"), "def")

    self.assertTrue(s.contains("abc"))

    l = list(s.iterate())
    self.assertEqual(l, ["abc"])

  def test_missing_item(self):
    s = self.store()

    self.assertFalse(s.contains("abc"))

    with self.assertRaises(NotFoundException):
      s.get("abc")

  def test_double_add(self):
    s = self.store()

    s.add("abc", "def")
    with self.assertRaises(Exception):
      s.add("abc", "ghi")

    self.assertEqual(s.get("abc"), "def")

  def test_update(self):
    s = self.store()

    s.add("abc", "def")
    self.assertEqual(s.get("abc"), "def")

    s.update("abc", "ghi")

    self.assertEqual(s.get("abc"), "ghi")

  def test_update_missing_row(self):
    s = self.store()

    self.assertFalse(s.contains("abc"))
    with self.assertRaises(NotFoundException):
      s.update("abc", "def")

  def test_iterate(self):
    s = self.store()

    s.add("a1", " a1")
    s.add("a2", " a2")
    s.add("a3", " a3")
    s.add("a4", " a4")
    s.add("a5", " a5")

    s.add("b1", " b1")

    l = list(s.iterate(prefix="a"))
    self.assertEqual(l, ["a1", "a2", "a3", "a4", "a5"])
