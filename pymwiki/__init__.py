
import sys

from pymwiki.app import MwikiApp

def usage():
  print("mwiki <command> ...")
  print("  init d [n] - initialize an mwiki with root directory $d,")
  print("               store mwiki contents in directory $n (defaults to $d)")
  print("  edit n     - edit the entry called $n")
  print("  entries    - list all of the wiki entries")
  print("  browse n   - open the wiki entry called $n")


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
    "graph": lambda m, y: m.graph(),
  }

  if len(sys.argv) <= 1:
    usage()
    return

  _bin, command, *args = sys.argv

  if command == "init":
    MwikiApp.create(*args)
  elif command in WIKI_COMMANDS:
    mw = MwikiApp.find()
    WIKI_COMMANDS[command](mw, args)
  else:
    raise Exception("error: '{}' is not an mwiki command".format(command))

