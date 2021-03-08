#!/usr/bin/env python3

from contextlib import closing
import sqlite3

from src.exceptions import NotFoundException

class NoDefault:
  pass

class Storage:
  @staticmethod
  def open(filename):
    return Storage(sqlite3.connect(filename, isolation_level=None))

  def __init__(self, dbconn):
    self.conn = dbconn

    with self.cursor() as c:
      c.execute("PRAGMA case_sensitive_like = ON;")
      c.execute("""CREATE TABLE IF NOT EXISTS Storage (
                    name BYTES PRIMARY KEY,
                    content BYTES
                  );""")

  def cursor(self):
    return closing(self.conn.cursor())

  def __row_val(self, c, entry, default=NoDefault):
    row = c.fetchone()
    if not row:
      if default == NoDefault:
        raise NotFoundException("Could not find: {}".format(entry))
      return default
    return row[0]

  def __contains(self, entry):
    with self.cursor() as c:
      c.execute("SELECT 1 FROM Storage WHERE name = ?;", (entry,))
      self.__row_val(c, entry)

  def contains(self, entry):
    try:
      self.__contains(entry)
      return True
    except NotFoundException:
      return False

  def get(self, entry, default=NoDefault):
    """Fetch the key if it exists.

    Returns the default if one is provided, otherwise throws an exception.
    """
    with self.cursor() as c:
      c.execute("SELECT content FROM Storage WHERE name = ?;", (entry,))
      return self.__row_val(c, entry, default)

  def put(self, entry, content):
    "Add or update the key"
    with self.cursor() as c:
      c.execute("INSERT OR REPLACE INTO Storage (name, content) VALUES (?, ?);", (entry, content))
      return c.lastrowid

  def remove(self, entry):
    "Removes the key if it exists."
    with self.cursor() as c:
      c.execute("DELETE FROM Storage WHERE name = ?;", (entry,))

  def iterate(self, prefix=None):
    """Returns all the keys for items in storage.

    Takes an optional prefix to limit the items returned.
    """
    with self.cursor() as c:
      if not prefix:
        c.execute("SELECT name FROM Storage;")
      else:
        prefix = "{}%".format(prefix)
        c.execute("SELECT name FROM Storage WHERE name LIKE ?;", (prefix,))

      for row in c:
        yield row[0]
