import unittest
import sqlite3
from pymwiki.manager import Builder, Manager, RecordingStorage, ManagedStorage
from pymwiki.exceptions import NotFoundException

class TestStorage:
  def __init__(self):
    self.calls = []
  def contains(self, entry):
    self.calls.append(("contains", entry))
    return "contains"
  def get(self, entry, default):
    self.calls.append(("get", entry, default))
    return "get"
  def iterate(self, prefix=None):
    self.calls.append(("iterate", prefix))
    return ["iterate"]
  def put(self, entry, content):
    self.calls.append(("put", entry, content))
  def remove(self, entry):
    self.calls.append(("remove", entry))

# Duck tying for the win...
class RecordingStorageTests(unittest.TestCase):
  def test_contains(self):
    r = RecordingStorage(t := TestStorage())

    self.assertEqual(r.contains("abc"), "contains")
    self.assertEqual(t.calls, [("contains", "abc")])

  def test_get(self):
    r = RecordingStorage(t := TestStorage())
    self.assertEqual(r.get("abc", "123"), "get")
    self.assertEqual(t.calls, [("get", "abc", "123")])

  def test_iterate(self):
    r = RecordingStorage(t := TestStorage())
    self.assertEqual(list(r.iterate(prefix="abc")), ["iterate"])
    self.assertEqual(t.calls, [("iterate", "abc")])

  def test_put(self):
    r = RecordingStorage(t := TestStorage())
    with self.assertRaises(Exception):
      r.put("abc", "def")

  def test_remove(self):
    r = RecordingStorage(t := TestStorage())
    with self.assertRaises(Exception):
      r.remove("abc")


class DagShim:
  def __init__(self, deps):
    self.deps = deps
    self.changed = None

  def has_dependencies(self, key):
    return self.deps

  def mark_changed(self, entry):
    self.changed = entry


class ManagedStorageTests(unittest.TestCase):
  def test_passthrough(self):
    m = ManagedStorage(t := TestStorage(), None)

    self.assertEqual(m.contains("abc"), "contains")
    self.assertEqual(m.get("abc", "def"), "get")
    self.assertEqual(list(m.iterate(prefix="abc")), ["iterate"])

    self.assertEqual(t.calls, [("contains", "abc"), ("get", "abc", "def"), ("iterate", "abc")])

  def test_remove(self):
    m = ManagedStorage(None, None)

    with self.assertRaises(Exception):
      m.remove("abc")

  def test_put_with_dependencies(self):
    m = ManagedStorage(t := TestStorage(), d := DagShim(True))

    with self.assertRaises(Exception):
      m.put("abc", "def")

  def test_put_without_dependencies(self):
    m = ManagedStorage(t := TestStorage(), d := DagShim(False))

    m.put("abc", "def")

    self.assertEqual(t.calls, [("put", "abc", "def")])
    self.assertEqual(d.changed, "abc")
    


class ManagerTests(unittest.TestCase):
  def m(self, builder=None):
    return Manager.open(":memory:", builder)

  def test_clean(self):
    m = self.m()

    m.add("abc")
    m.add("def")
    m.add("ghi")

    # Adding nodes doesn't update storage.
    # This assertion is for documentation purposes only.
    self.assertEqual(list(m.storage.iterate()), [])

    s = m.storage
    s.put("abc", "abc-val")
    s.put("def", "def-val")
    s.put("ghi", "ghi-val")
    self.assertEqual(list(m.storage.iterate()), ["abc", "def", "ghi"])

    m.clean() # no deps, no-op
    self.assertEqual(list(m.storage.iterate()), ["abc", "def", "ghi"])

    m.add_dependency("def", "abc")
    m.add_dependency("ghi", "def")

    m.clean()
    self.assertEqual(list(m.storage.iterate()), ["abc"])

  def test_simple_build(self):
    class Builder:
      def build(s, target, storage, deps_func):
        if target == "abc":
          self.assertEqual(deps_func(), set())
        elif target == "def":
          self.assertEqual(deps_func(), set(["abc"]))
        elif target == "ghi":
          self.assertEqual(deps_func(), set(["def"]))
        return target + "-built-value"

    m = self.m(Builder())
    s = m.storage

    m.add("abc")
    m.add("def")
    m.add("ghi")
    s.put("abc", "abc-val")
    s.put("def", "def-val")
    s.put("ghi", "ghi-val")
    m.add_dependency("def", "abc")
    m.add_dependency("ghi", "def")

    m.build()

    self.assertEqual(s.get("abc"), "abc-built-value")
    self.assertEqual(s.get("def"), "def-built-value")
    self.assertEqual(s.get("ghi"), "ghi-built-value")

  def test_bad_build(self):
    class Builder:
      def build(s, target, storage, deps_func):
        storage.get("abc", None)
        return target + "-val"

    m = self.m(Builder())
    s = m.storage

    m.add("abc")
    m.add("def")
    m.build("abc")

    with self.assertRaises(Exception):
      m.build("def")
