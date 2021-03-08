#!/usr/bin/env python3

from contextlib import closing
import collections
import enum
import sqlite3

from src.exceptions import NotFoundException

class BuildStatus(enum.IntEnum):
  # you can not change these values, they're serialized to disk.
  BUILT = 1
  CHANGED = 2


class DependencyGraph:
  """Directed Acyclic Graph structure.

  Stored such that a -> b means if a is changed, b must be updated.
  """
  @staticmethod
  def open(dbfile):
    return DependencyGraph(sqlite3.connect(dbfile, isolation_level=None))

  def __init__(self, dbconn):
    self.conn = dbconn
    with self.cursor() as c:
      c.execute("PRAGMA foreign_keys = ON;")
      # Triggers cause cascading changes.
      c.execute("PRAGMA recursive_triggers = ON;")
      c.execute("""CREATE TABLE IF NOT EXISTS Nodes (
                      rowid INTEGER PRIMARY KEY,
                      status INTEGER DEFAULT (2),
                      name BYTES);""")
      c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS Nodes_name ON Nodes (name);""")
      c.execute("""CREATE TABLE IF NOT EXISTS Edges (
                      from_id INTEGER NOT NULL,
                      to_id INTEGER NOT NULL,
                      PRIMARY KEY (from_id, to_id) ON CONFLICT IGNORE,
                      FOREIGN KEY (from_id) REFERENCES Nodes(rowid) ON DELETE CASCADE,
                      FOREIGN KEY (to_id) REFERENCES Nodes(rowid) ON DELETE CASCADE
                  ) WITHOUT ROWID;""")
      c.execute("CREATE INDEX IF NOT EXISTS Edges_to ON Edges (to_id);")
      # On marking anything as changed, cascade through all the dependencies.
      c.execute("""CREATE TRIGGER IF NOT EXISTS NodeChanged
                      AFTER UPDATE OF status ON Nodes
                      WHEN NEW.status = 2
                      BEGIN
                        UPDATE Nodes SET status = 2
                        WHERE Nodes.rowid IN (SELECT to_id FROM Edges WHERE from_id = NEW.rowid);
                      END;""")
      # Check immediate dependencies to see if they're built.
      c.execute("""CREATE TRIGGER IF NOT EXISTS NodeMarkedBuilt
                      BEFORE UPDATE OF status ON Nodes
                      WHEN NEW.status = 1
                      BEGIN
                        SELECT
                          CASE COUNT(from_id)
                            WHEN 0 THEN 0
                            ELSE RAISE(FAIL, "Depends on things not built.")
                          END
                        FROM Edges INDEXED BY Edges_to
                        JOIN Nodes ON rowid = from_id
                        WHERE status != 1 AND to_id = NEW.rowid;
                      END;""")
      # Catch updates to edges too.
      # If you change these triggers to use "BEFORE" instead of "AFTER" then
      # they won't catch cycles being added to the graph, as the NodesChanged
      # trigger will just stop.
      c.execute("""CREATE TRIGGER IF NOT EXISTS EdgeCreate
                      AFTER INSERT ON Edges
                      BEGIN
                        UPDATE Nodes SET status = 2
                        WHERE Nodes.rowid = NEW.to_id;
                      END;""")
      c.execute("""CREATE TRIGGER IF NOT EXISTS EdgeDelete
                      AFTER DELETE ON Edges
                      BEGIN
                        UPDATE Nodes SET status = 2
                        WHERE Nodes.rowid = OLD.to_id;
                      END;""")

  def cursor(self):
    return closing(self.conn.cursor())

  def __id(self, entry):
    with self.cursor() as c:
      c.execute("SELECT rowid FROM Nodes INDEXED BY Nodes_name WHERE name = ?", (entry,))
      row = c.fetchone()
      if not row:
        raise NotFoundException("Could not find: {}".format(entry))
      return row[0]

  def add(self, entry):
    """Add an entry to the dependency graph.


    Returns the numeric id of the item.
    """
    with self.cursor() as c:
      try:
        return self.__id(entry)
      except NotFoundException:
        c.execute("INSERT INTO Nodes (name) VALUES (?);", (entry,))
        return c.lastrowid

  def remove(self, entry, load_connected=True):
    """Removes the entry.

    Returns a tuple of this entries depedencies and dependants so they can be
    cleaned up as necessary. Because dependencies are removed, all the
    dependants are marked as changed.
    """
    with self.cursor() as c:
      i = self.__id(entry)

      deps = None
      rdeps = None
      if load_connected:
        c.execute("SELECT name FROM Edges INDEXED BY Edges_to JOIN Nodes ON rowid = from_id WHERE to_id = ?;", (i,))
        deps = []
        for row in c:
          deps.append(row[0])
        c.execute("SELECT name FROM Edges JOIN Nodes ON rowid = to_id WHERE from_id = ?;", (i,))
        rdeps = []
        for row in c:
          rdeps.append(row[0])

      c.execute("DELETE FROM Nodes WHERE rowid = ?", (i,))
      return (deps, rdeps)

  def edge(self, entry_from, entry_to):
    with self.cursor() as c:
      from_id = self.__id(entry_from)
      to_id = self.__id(entry_to)
      c.execute("INSERT INTO Edges (from_id, to_id) VALUES (?, ?);", (from_id, to_id))

  def status(self, entry):
    with self.cursor() as c:
      c.execute("SELECT status FROM Nodes INDEXED BY Nodes_name WHERE name = ?;", (entry,))
      row = c.fetchone()
      if not row:
        raise NotFoundException("Could not find: {}".format(entry))
      return BuildStatus(row[0])

  def changed(self):
    """Returns the set of all items that are currently marked as changed."""
    with self.cursor() as c:
      changed = set()
      c.execute("SELECT name FROM Nodes WHERE status = 2;")
      for row in c:
        changed.add(row[0])
      return changed

  def has_dependencies(self, target):
    with self.cursor() as c:
      i = self.__id(target)
      c.execute("SELECT EXISTS (SELECT 1 FROM Edges INDEXED BY Edges_to WHERE to_id = ?);", (i,))
      return bool(c.fetchone()[0])

  def dependencies(self, target, deps_of_deps=False):
    deps = set()
    with self.cursor() as c:
      i = self.__id(target)
      c.execute("""SELECT name
                    FROM Edges INDEXED BY Edges_to
                    JOIN Nodes ON rowid = from_id
                    WHERE to_id = ?;""", (i,))
      for row in c:
        deps.add(row[0])

      if deps_of_deps:
        second_deps = set()
        for d in deps:
          second_deps.update(self.dependencies(d, deps_of_deps=False))

        deps.update(second_deps)

      return deps

  def __load_dep_edges(self, target):
    deps = {}
    lookup = set([target])
    seen = set()

    with self.cursor() as c:
      while len(lookup) > 0:
        next_id = lookup.pop()
        seen.add(next_id)

        c.execute("""SELECT from_id
                      FROM Edges INDEXED BY Edges_to
                      JOIN Nodes ON rowid = from_id
                      WHERE to_id = ? AND status != 1;""", (next_id,))

        deps[next_id] = set()
        for row in c:
          child = row[0]
          deps[next_id].add(child)
          if child not in seen:
            lookup.add(child)

    return deps

  def __load_all_edges(self):
    deps = {}
    lookup = set()
    with self.cursor() as c:
      # Load all unbuilt items
      c.execute("SELECT rowid FROM Nodes WHERE status != 1;")
      for row in c:
        rowid = row[0]
        lookup.add(rowid)
        deps[rowid] = set()

      # load all their edges.
      for item in lookup:
        c.execute("""SELECT to_id
                      FROM Edges
                      JOIN Nodes ON rowid = to_id
                      WHERE from_id = ? AND status != 1;""", (item,))
        for row in c:
          deps[row[0]].add(item)

    return deps

  def rebuild_instructions(self, target=None):
    """Return all items that need rebuilding for the target, or all of them if no target is supplied.

    These are returned in dependency order, meaning that rebuilding items in
    the order they are returned will result in a correct build.
    """
    deps = None
    if target:
      deps = self.__load_dep_edges(self.__id(target))
    else:
      deps = self.__load_all_edges()

    # Topological sort on deps.
    out = []
    processing = set()
    lookup = set(deps.keys())

    def visit(rowid):
      if rowid in processing:
        # Sqlite should protect us from this, but just to be sure.
        raise Exception("Dependency Graph has a cycle!")
      elif rowid not in lookup:
        return

      lookup.remove(rowid) # don't process the node again.
      processing.add(rowid) # catch a cycle.

      for c in deps[rowid]:
        visit(c)

      processing.remove(rowid)
      out.append(rowid)

    while len(lookup) > 0:
      next_id = lookup.pop() # pick something arbitrary.
      lookup.add(next_id) # put it back.
      visit(next_id)

    # Map ids back to user keys.
    with self.cursor() as c:
      for o in out:
        c.execute("SELECT name FROM Nodes WHERE rowid = ?;", (o,))
        yield c.fetchone()[0]

  def __mark(self, entry, status):
    with self.cursor() as c:
      entry_id = self.__id(entry)
      c.execute("UPDATE Nodes SET status = ? WHERE Nodes.rowid = ?;", (status.value, entry_id))

  def mark_changed(self, entry):
    """Mark the entry as having changed, and needing to be rebuilt.

    This propagates to everything that depends on this entry.
    """
    self.__mark(entry, BuildStatus.CHANGED)

  def mark_rebuilt(self, entry):
    """Mark the entry as having been rebuilt.

    Raises an exception if something that this entry depends on is marked as
    changed.
    """
    self.__mark(entry, BuildStatus.BUILT)



