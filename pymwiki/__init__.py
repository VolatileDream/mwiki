#!/usr/bin/env python3

import os
import pathlib
import shutil
import subprocess
import sys

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


class Mwiki:
  @staticmethod
  def find():
    return Mwiki(mwiki_require())

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

    return Mwiki({
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

  def browse(self, entry=None):
    if not entry:
      entry = "#.html"
    elif not entry.endswith("html"):
      entry = "{}.html".format(entry)

    html = self.path.joinpath("out-html").absolute()
    subprocess.run(["sensible-browser", entry], cwd=str(html), check=True)

  def edit(self, entry):
    if not entry:
      raise Exception("Can't create the empty entry.")

    path = self.path

    entryp = path.joinpath("entries", "{}.mw".format(entry))
    existed = entryp.exists()

    if not sys.stdin.isatty():
      with entryp.open(mode='wb') as io_out:
        # ideally here we'd use something like os.sendfile,
        # but it isn't suited for use with stdin.
        io_in = sys.stdin.detach()
        buf = bytearray(2 << 16)
        while (read := io_in.readinto(buf)) != None:
          io_out.write(buf[:read])
    else:
      if not existed:
        resp = input("'{}' doesn't exist, create it? (Y/n) ".format(entry))
        if resp in ('n', 'N'):
          return 1

      args = ["sensible-editor", "{}.mw".format(entry)]
      subprocess.run(args, cwd=str(entryp.parent), check=True)
      

    # ugly hack. workaround for tup wildcards not picking up
    # new files when an existing input file isn't modified.
    if existed != entryp.exists():
      out = path.joinpath("out-html")
      # delete index
      out.joinpath("#.html").unlink(missing_ok=True)
      # special meta files that are known to exist as aggregates.
      for p in out.glob("~*"):
        p.unlink()

    self.build()

  def entries(self, reverse=False):
    path = self.path.joinpath("entries")
    entries = list()
    for p in path.rglob("*.mw"):
      entries.append(p.name[:-3])
    entries.sort(key=lambda x: x.upper(), reverse=reverse)
    for e in entries:
      print(e)

  def build(self, auto=False, daemon=False):
    args = ["tup"]
    if daemon:
      args.extend(["monitor", "--foreground"])
    if auto:
      args.extend(["--autoparse", "--autoupdate"])

    subprocess.run(args, cwd=str(self.path), check=True)


def usage():
  print("mwiki <command> ...")
  print("  init d [n] - initialize an mwiki with root directory $d,")
  print("               store mwiki contents in directory $n (defaults to $d)")
  print("  edit n     - edit the entry called $n")
  print("  entries    - list all of the wiki entries")
  print("  browse n   - open the wiki entry called $n")
  print("  build [-d|--daemon [-a|--auto]] - start a build")
  print("    -d, --daemon - file monitoring daemon, makes builds faster")
  print("    -a, --auto - make the daemon rebuild on edits")


def main():
  # stupid hack to avoid argparse.
  def f(args, *names):
    # return val if one of names is present in args.
    names = set(names)
    for a in args:
      if a in names:
        return True
    return False

  WIKI_COMMANDS = {
    "edit": lambda m, y: m.edit(*y),
    "browse": lambda m, y: m.browse(*y),
    "entries": lambda m, y: m.entries(reverse=f(y, "-r", "--reverse")),
    "build": lambda m, y: m.build(auto=f(y, "-a", "--auto"), daemon=f(y, "-d", "--daemon")),
  }

  if len(sys.argv) <= 1:
    usage()
    return

  _bin, command, *args = sys.argv

  if command == "init":
    Mwiki.create(*args)
  elif command in WIKI_COMMANDS:
    mw = Mwiki.find()
    WIKI_COMMANDS[command](mw, args)
  else:
    raise Exception("error: '{}' is not an mwiki command".format(command))


if __name__ == "__main__":
  main()