#!/usr/bin/env python3

from contextlib import closing
import sqlite3

from src.exceptions import NotFoundException

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

  def __row(self, c, entry):
    row = c.fetchone()
    if not row:
      raise NotFoundException("Could not find: {}".format(entry))
    return row

  def __contains(self, entry):
    with self.cursor() as c:
      c.execute("SELECT 1 FROM Storage WHERE name = ?;", (entry,))
      self.__row(c, entry)

  def contains(self, entry):
    try:
      self.__contains(entry)
      return True
    except NotFoundException:
      return False

  def get(self, entry):
    with self.cursor() as c:
      c.execute("SELECT content FROM Storage WHERE name = ?;", (entry,))
      return self.__row(c, entry)[0]

  def add(self, entry, content):
    with self.cursor() as c:
      c.execute("INSERT INTO Storage (name, content) VALUES (?, ?);", (entry,content))
      return c.lastrowid

  def update(self, entry, content):
    with self.cursor() as c:
      self.__contains(entry)
      c.execute("UPDATE Storage SET content = ? WHERE name = ?;", (content,entry))

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
