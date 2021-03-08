#!/usr/bin/env python3

# quick generic builder

import sqlite3

from pymwiki.dag import DependencyGraph
from pymwiki.storage import Storage, NoDefault

class RecordingStorage:
  """Storage interface that exists to record the changes made to storage.

  Passed to the Builder function that users provide to ensure they aren't
  changing things they shouldn't be.
  """
  def __init__(self, storage):
    self.storage = storage
    self.read = set()

  def contains(self, entry):
    self.read.add(entry)
    return self.storage.contains(entry)

  def get(self, entry, default=NoDefault):
    self.read.add(entry)
    return self.storage.get(entry, default)

  def iterate(self, prefix=None):
    for k in self.storage.iterate(prefix):
      self.read.add(k)
      yield k

  def put(self, entry, content):
    raise Exception("Can not perform writes during Builder invocation.")

  def remove(self, entry):
    raise Exception("Can not perform writes during Builder invocation.")


class ManagedStorage:
  """Storage interface that writes back updates to the Manager DependenyGraph.

  Returned to the user of the Manager to ensure that Storage updates are
  correctly reflected in the DependencyGraph state.
  """
  def __init__(self, storage, dag):
    self.storage = storage
    self.dag = dag

  def contains(self, entry):
    return self.storage.contains(entry)

  def get(self, entry, default=NoDefault):
    return self.storage.get(entry, default)

  def iterate(self, prefix=None):
    return self.storage.iterate(prefix)

  def put(self, entry, content):
    if self.dag.has_dependencies(entry):
      raise Exception("Can not write to generated item: {}".format(entry))
    self.dag.mark_changed(entry)
    return self.storage.put(entry, content)

  def remove(self, entry):
    raise Exception("Removal via storage doesn't do what you expect, did you intend to use Manager.remove instead?")


class Builder:
  def build(self, target, storage, deps_func):
    pass


class Manager:
  @staticmethod
  def open(dbfile, builder):
    dbconn = sqlite3.connect(dbfile, isolation_level=None)
    return Manager(dbconn, Storage(dbconn), DependencyGraph(dbconn), builder)

  def __init__(self, dbconn, storage, dag, builder):
    self.dbconn = dbconn
    self.storage = storage
    self.dag = dag
    self.builder = builder

  def __bad_touch(self, name, touched):
    # We're lenient, because we allow them to touch dependencies of their
    # dependencies. This is convenient for creating fake nodes to aggregate
    # others for graph optimization.

    lenient = True  # TODO: consider not being lenient.

    deps = self.dag.dependencies(name, deps_of_deps=lenient)
    deps.add(name)
    bad_touch = touched.difference(deps)
    if len(bad_touch) > 0:
      raise Exception("While building '{}' the builder accessed non-dependencies: {}".format(name, ", ".join(bad_touch)))

  def __build(self, name):
    s = RecordingStorage(self.storage)

    content = self.builder.build(name, s, lambda: self.dag.dependencies(name))

    # Check if the builder accessed things they should not have.
    self.__bad_touch(name, s.read)

    return content

  def build(self, name=None):
    """Build everything or `name` and it's dependencies.

    Invokes the supplied builder in dependency order to build items.
    """
    rebuild = self.dag.rebuild_instructions(name)
    for name in rebuild:
      content = self.__build(name)
      if content is None:
        self.storage.remove(name)
      else:
        self.storage.put(name, content)

  def clean(self):
    """Deletes all generated items that need rebuilding.

    Note that **nodes that have dependencies** are considered to be generated.

    There is no need to ever invoke this function for a correct build, as the
    underlying storage and dependency management ensure correctness.
    """
    for key in self.dag.changed():
      if self.dag.has_dependencies(key):
        self.storage.remove(key)

  def transaction(self):
    """Wraps actions in a transaction, use for better performance.

    Returns an opaque Context Manager object.
    """
    return self.dbconn

  def storage(self):
    "Returns the Storage interface."
    return ManagedStorage(self.storage, self.dag)

  def add(self, name):
    "Add an item to the dependency graph."
    self.dag.add(name)

  def remove(self, name, load_connected=True):
    """Remove an item from the dependency graph, also removes it from storage.

    Returns a tuple of ([dependencies], [dependants]) if load_connected is True,
    otherwise returns (None, None).
    """
    self.storage.remove(name)
    deps, rdeps = self.dag.remove(name, load_connected=load_connected)
    return (deps, rdeps)

  def add_dependency(self, name, dependency):
    """Adds a dependency to name.

    Because this changes the dependency set for `name`, name gets marked as
    changed and needing rebuild.    
    """
    self.dag.edge(dependency, name)
