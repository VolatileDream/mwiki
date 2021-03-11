#!/usr/bin/env python3

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from pymwiki.builder import MwikiBuilder
from pymwiki.manager import Manager

WIKI_FILE = ".mwiki"
PROJECT = "MWIKI_PROJECT"
PATH = "MWIKI_PATH"

def find_root_file():
  # absolute current path
  current = pathlib.Path().absolute()

  while True:
    check = current.joinpath(WIKI_FILE)
    if check.exists():
      return check

    # Stop after checking the root directory
    if current == current.parent:
      raise Exception("No mwiki config file found")

    current = current.parent


def mwiki_require():
  config = find_root_file()

  with config.open() as f:
    settings = {PROJECT: str(config.parent)}

    for line in f:
      line = line.strip()
      if line.startswith("#") or not line:
        continue
      key, val = line.split("=", maxsplit=1)

      if key in settings:
        raise Exception("Entry already exists in config: {}".format(key))
      settings[key] = val

    return settings


class MwikiApp:
  @staticmethod
  def find():
    return MwikiApp(mwiki_require())

  @staticmethod
  def create(projectdir, wikidir=None):
    project = pathlib.Path(projectdir).absolute() # must always be absolute.

    wiki = project # by default
    if wikidir is not None:
      wiki = pathlib.Path(wikidir)

    config = project.joinpath(WIKI_FILE)
    if config.exists():
      raise Exception("Configuration file already exists: {}".format(config))

    project.mkdir(parents=True, exist_ok=True)
    with config.open(mode='w') as f:
      f.write("{} = {}".format(PATH, wiki))

    wiki.mkdir(parents=True, exist_ok=True)

    base_install = pathlib.Path(sys.argv[0]).parent.joinpath("base_install")
    if not base_install.exists():
      print("Could not find mwiki git repo.")
      print("You will have to install the mwiki base_install into {} yourself".format(wiki))
      print(" mwiki can be found here: https://github.com/VolatileDream/mwiki/tree/master/base_install")
    else:
      print("Copying {} into {}".format(base_install, wiki))
      shutil.copytree(str(base_install), str(wiki), dirs_exist_ok=True)

    return MwikiApp({
      PATH: str(wiki),
      PROJECT: str(project),
    })

  @property
  def path(self):
    p = pathlib.Path(self.config[PATH])
    if not p.is_absolute():
      p = pathlib.Path(self.config[PROJECT]).joinpath(p)
    return p

  def __init__(self, config):
    self.config = config
    self.builder = None

  def __b(self):
    if self.builder is None:
      m = Manager.open(self.path.joinpath("db.sqlite"))
      self.builder = MwikiBuilder(self.path, m)
    return self.builder

  def browse(self, entry=None):
    self.__b().run(entry)

    if not entry:
      entry = "#"

    html = self.path.joinpath("out-html")

    subprocess.run(["sensible-browser", "{}.html".format(entry)], cwd=str(html), check=True)

  def edit(self, entry):
    if not entry:
      raise Exception("Can't create the empty entry.")

    content = None
    if not sys.stdin.isatty():
      content = sys.stdin.read()
      self.__b().put(entry, content)
    else:
      if not self.__b().contains(entry):
        resp = input("'{}' doesn't exist, create it? (Y/n) ".format(entry))
        if resp in ('n', 'N'):
          return 1

      self.__b().edit_entry(entry, lambda x: subprocess.run(["sensible-editor", x], check=True))

  def entries(self, reverse=False):
    entries = self.__b().entries()
    if reverse:
      entries.reverse()
    for e in entries:
      print(e)

  def graph(self):
    for n1, n2 in self.__b().graph():
      print(n1, "->", n2)
    
