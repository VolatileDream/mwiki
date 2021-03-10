#!/usr/bin/env python3

# quick pseudo written builder for mwiki
import os
import sys
from hashlib import sha512
from pathlib import Path
from tempfile import NamedTemporaryFile

from pymwiki.manager import Manager, Builder
from pymwiki.plugins import Plugin, DirectiveHandling, DirectivePlugin, MetaPageMixin, RenderMixin
from pymwiki.template import Template

CONFIG_FILE = "config.py"
TEMPLATE_FILE = "template.tmpl"
PLUGIN_DIR = "plugins"

RESERVED_PLUGINS = frozenset(["name", "content", "impl"])

def k(name):
  return name
  return name.replace("\0", ":")

def n(*args, end=False):
  "Convert the arguments to a storage name"
  suffix = ""
  if end:
    suffix = ":"
  return ":".join(args) + suffix

def f(name):
  "Convert from a storage key back to an argument array."
  return name.split(":")

def loader(path):
  return path.open()


class MwikiBuilder:
  """Wraps Storage and DependencyGraph to handle building and rendering pages."""
  def __init__(self, rootpath : Path, manager : Manager, path_loader=loader):
    self.root = rootpath
    self.manager = manager
    self.manager.set_builder(self)
    self.load = path_loader

    # Lazy loaded attributes
    self.checked_fs = False
    self.config_imported = False
    self.tmpl = None
    self.plugins = {}

    # Build some nodes (not created if they exist)
    self.manager.add(n("index")) # index file
    self.manager.add(n("template")) # template file.
    self.manager.add(n("config.py")) # configuration for plugins

    self.manager.add(n("render")) # "rendered" template node.
    self.manager.add(n("config")) # aggregate config node
    self.manager.add_dependency("config", "template")
    self.manager.add_dependency("config", "config.py")
    self.manager.add_dependency("render", "config")

  def __template(self, reload=False):
    """Fetch the template.

    Loads the template from file if necessary, or reloads on request.
    """
    if self.tmpl is None or reload:
      with self.load(self.root.joinpath(TEMPLATE_FILE)) as f:
        self.tmpl = Template.parse(f.read())
    return self.tmpl

  def __validate_template(self):
    # Load and validate the template, it was marked as changed as must be reloaded.
    t = self.__template(reload=True)
    missing = set()
    for v in t.variables():
      p = self.plugins.get(v, None)
      if not p and v not in RESERVED_PLUGINS:
        missing.add(v)
    if missing:
      raise Exception("bad template references plugins that don't exist: {}".format(", ".join(missing)))

  def __build_plugin(self, key, storage, deps_func):
    _p, name, instr, *entry = f(key)

    if name == "impl":
      # formality.
      return storage.get(key)

    plugin = self.plugins[name]
    if instr == "index" and len(entry) == 0:
      index = {}
      for index_key in filter(lambda x: x.startswith(key), deps_func()):
        _plugin, _pname, _index, name = f(index_key)
        content = storage.get(index_key, None)
        if content:
          index[name] = content
      return plugin.aggregate_index(index)

    elif instr == "index" and len(entry) == 1:
      content = storage.get(n("entry", entry[0]))
      partial = plugin.compute_partial_index(entry[0], content)
      return partial

    elif instr == "meta":
      index = storage.get(n("plugin", name, "index"))
      return plugin.render_metapage(index)

    elif instr == "render":
      index = storage.get(n("plugin", name, "index"))
      return plugin.get_content(entry[0], index)

    else:
      raise Exception("Building plugin: {} not implemented".format(repr(name)))

  def build(self, name, storage, deps_func):
    instr, *args = f(name)

    if (instr == "render" or instr == "config") and len(args) == 0:
      # fake nodes to tie configuration to the build
      return None

    if instr == "entry":
      return storage.get(name)

    elif instr == "config.py":
      self.import_config()
      return None

    elif instr == "template":
      self.__validate_template()
      return storage.get(name)

    elif instr == "html":
      entry, *empty = args
      if entry.startswith("~"):
        content = storage.get(n("plugin", entry[1:], "meta"))
      else:
        content = storage.get(n("render", entry))
      return self.plugins["html"].get_content(entry, content)

    elif instr == "index":
      entries = set()
      for key in deps_func():
        _e, name = f(key)
        entries.add(name)

      html_dir = self.root.joinpath("out-html")
      html_dir.mkdir(exist_ok=True)

      content = self.plugins["index"].get_content("index", entries)

      with html_dir.joinpath("#.html").open("w") as file:
        file.write(content)

      return None

    elif instr == "file":
      entry, *empty = args
      content = storage.get(n("html", entry))

      html_dir = self.root.joinpath("out-html")
      html_dir.mkdir(exist_ok=True)

      with html_dir.joinpath("{}.html".format(entry)).open("w") as file:
        file.write(content)

      return None # these nodes don't have data stored.

    elif instr == "render":
      entry, *empty = args
      content = storage.get(n("entry", entry))

      for p in self.plugins:
        if not self.plugins[p].is_directive():
          continue
        content = DirectivePlugin.rewrite_content(content, self.plugins[p])

      t = self.__template()
      binds = { "name": entry, "content": content}
      for v in t.variables():
        # Assume all the plugins exist, sanity checking
        # the template should have been done elsewhere.
        # But do a little check to skip name and content binds.
        if v not in binds:
          binds[v] = storage.get(n("plugin", v, "render", entry))
      return self.__template().render(**binds)

    elif instr == "plugin":
      return self.__build_plugin(name, storage, deps_func)

    else:
      raise Exception("Building {} not implemented".format(repr(name)))

  def __rm_plugin(self, name):
    self.manager.remove(n("plugin", "impl", name), load_connected=False)

    if self.manager.contains(n("plugin", name, "meta")):
      self.manager.remove(n("plugin", name, "meta"), load_connected=False)
      self.manager.remove(n("html", "~{}".format(name)))
      self.manager.remove(n("file", "~{}".format(name)))

    index = n("plugin", p.name(), "index")
    index_prefix = n("plugin", p.name(), "index", end=True)

    deps, rdeps = self.manager.remove(index, load_connected=True)
    for d in deps:
      # these should all be ("plugin", name, "index", entry) values.
      if not d.startswith(index_prefix):
        raise Exception("Found '{}' as a dependency of (plugin, {}, index)".format(repr(d), p.name()))

      self.manager.remove(d, load_connected=False)

    # We don't have the plugin to check if it had render output.
    render_prefix = n("plugin", p.name(), "render", end=True)
    for d in rdeps:
      if not d.startswith(render_prefix):
        continue
      self.manager.remove(d, load_connected=False)

  def __add_plugin(self, p):
    # So many edges get updated when we add plugins.

    # node to denote the .py file for the plugin, it will never have dependencies.
    # except for this key, all other plugin keys are of the form ("plugin", name, type, ...)
    # using ("plugin", "impl", ...) allows discovering the existing plugins.
    self.manager.add(n("plugin", "impl", p.name()))
    self.manager.add_dependency("config", n("plugin", "impl", p.name()))

    # Load change detection data, only works after we add the plugin to the Manager.
    self.__check_plugin(p.name())

    # Special plugins, exempt from normal rules.
    if p.name() in ["html", "index"]:
      return

    # fake node used to link things to the plugins index.
    self.manager.add(n("plugin", p.name(), "index"))

    self.manager.add_dependency(n("plugin", p.name(), "index"), n("plugin", "impl", p.name()))

    if p.has_meta():
      meta_page = "~{}".format(p.name())
      self.manager.add(n("plugin", p.name(), "meta"))
      self.manager.add(n("html", meta_page))
      self.manager.add(n("file", meta_page))
      self.manager.add_dependency(n("plugin", p.name(), "meta"), n("plugin", "impl", p.name()))
      self.manager.add_dependency(n("plugin", p.name(), "meta"), n("plugin", p.name(), "index"))
      self.manager.add_dependency(n("html", meta_page), n("plugin", p.name(), "meta"))
      self.manager.add_dependency(n("file", meta_page), n("html", meta_page))
      self.manager.add_dependency(n("index"), n("file", meta_page))

    if p.has_render():
      self.manager.add_dependency(n("render"), n("plugin", p.name(), "index"))

    for e in self.manager.storage().iterate(prefix=n("entry", end=True)):
      _entry, name = f(e)
      self.__link_entry_to_plugin(name, p)

  def __link_entry_to_plugin(self, entry, p):
    self.manager.add(n("plugin", p.name(), "index", entry)) # index entry for the plugin

    # entry content -> plugin index
    self.manager.add_dependency(n("plugin", p.name(), "index", entry), n("entry", entry))
    self.manager.add_dependency(n("plugin", p.name(), "index"), n("plugin", p.name(), "index", entry))

    # implementation to the index entry
    self.manager.add_dependency(n("plugin", p.name(), "index", entry), n("plugin", "impl", p.name()))

    if p.has_render():
      # generated content for the page. Done this way to cache it.
      self.manager.add(n("plugin", p.name(), "render", entry))
      self.manager.add_dependency(n("plugin", p.name(), "render", entry), n("plugin", p.name(), "index"))
      self.manager.add_dependency(n("render", entry), n("plugin", p.name(), "render", entry))

  def __create(self, entry):
    # So many graph edits...
    self.manager.add(n("entry", entry))
    self.manager.add(n("render", entry)) # rendered page
    self.manager.add(n("html", entry)) # html converted page
    self.manager.add(n("file", entry)) # html converted page
    # render edges
    self.manager.add_dependency(n("render", entry), n("entry", entry))
    self.manager.add_dependency(n("html", entry), n("render", entry))
    self.manager.add_dependency(n("file", entry), n("html", entry))
    self.manager.add_dependency(n("render", entry), n("render"))
    self.manager.add_dependency(n("index"), n("file", entry))

    # add plugin edges too.
    for p in self.plugins:
      self.__link_entry_to_plugin(entry, p)

  def __check_plugin(self, name):
    self.__check(n("plugin", "impl", name),
                 self.root.joinpath(PLUGIN_DIR, "{}.py".format(name)))

  def __check(self, key, filepath):
    digest = None
    with self.load(filepath) as f:
      hasher = sha512()
      for line in f:
        hasher.update(line.encode())
      digest = hasher.digest()

    prev = self.manager.storage().get(key, default=bytes())
    if digest != prev:
      self.manager.storage().put(key, digest)

  def check(self):
    """Check for changes in items that exist outside of storage.

    This is called automatically if it wasn't already called before a call to
    build. If the caller is aware that one of these items might have changed
    after a call to build (out of band changes) then they should call it again
    or incorrect builds will result.
    """

    self.checked_fs = True

    # Each of the names below is a valid storage key, but contains nothing
    # because their content is actually stored on the filesystem. So we store
    # versioning information in their place instead.
    
    self.__check("config.py", self.root.joinpath(CONFIG_FILE))
    self.__check("template", self.root.joinpath(TEMPLATE_FILE))
    for p in self.manager.storage().iterate(prefix=n("plugin", "impl", end=True)):
      _plugin, _impl, name = f(p)
      self.__check_plugin(name)

    html = self.root.joinpath("out-html")
    if not html.joinpath("#.html").exists():
      self.manager.changed("index")

    for p in self.manager.storage().iterate(prefix=n("file", end=True)):
      _f, entry = f(p)
      if not html.joinpath("{}.html".format(entry)).exists():
        self.manager.changed(p)

  def import_config(self):
    """Import the config file.
    
    Allows for importing multiple times in case of changes.
    """
    self.config_imported = True

    config = self.root.joinpath(CONFIG_FILE).absolute()
    plugin_dir = self.root.joinpath(PLUGIN_DIR).absolute()

    new_plugins = {}
    def add_plugin(p):
      if not isinstance(p, Plugin):
        raise Exception("Plugin {} does not subclass Plugin".format(p))
      new_plugins[p.name()] = p

    # lookup path is modified for importing the config
    old_path = sys.path
    cwd = os.getcwd()
    try:
      sys.path = [str(plugin_dir), *old_path]
      os.chdir(str(plugin_dir.parent))
      with self.load(config) as file:
        code = compile(file.read(), str(config), 'exec', optimize=2)
        exec(code, {}, {"register": add_plugin})
    finally:
      # make sure the path is restored
      sys.path = old_path
      os.chdir(cwd)

    # We may no longer have the code for the old plugins, and the config may
    # have changed and no longer lists them either. So we look at the keys
    # that are created while adding the plugins.
    old_plugins = set()
    for p in self.manager.storage().iterate(n("plugin", "impl", end=True)):
      _p, _i, name = f(p)
      old_plugins.add(name)
      
    # swap in new plugins for old ones.
    removed = old_plugins.difference(new_plugins.keys())
    added = set(new_plugins.keys()).difference(old_plugins)

    for name in RESERVED_PLUGINS:
      if name in added:
        raise Exception("Can't name a plugin '{}'".format(name))

    for p in removed:
      self.__rm_plugin(p)

    for p in added:
      if not self.root.joinpath(PLUGIN_DIR, "{}.py".format(p)).exists():
        raise Exception("Could not find plugins/{}.py".format(name))
      self.__add_plugin(new_plugins[p])

    self.plugins = new_plugins

  # Part of the interface for use with the app.

  def put(self, entry, content):
    key = n("entry", entry)
    if not self.manager.storage().contains(key):
      self.__create(entry)
    self.manager.storage().put(key, content)

  def contains(self, entry):
    key = n("entry", entry)
    return self.manager.storage().contains(key)

  def get(self, entry):
    key = n("entry", entry)
    return self.manager.storage().get(key, None)

  def entries(self):
    entries = []
    for key in self.manager.storage().iterate(n("entry", end=True)):
      _e, entry = f(key)
      entries.append(entry)
    entries.sort(key=lambda x: x.upper())
    return entries

  def edit_entry(self, entry, editor_callback):
    key = n("entry", entry)
    with NamedTemporaryFile() as f:
      val = self.manager.storage().get(key)
      if val:
        t.write(val)
        t.flush()
      editor_callback(f.name)
      val = f.read()
      if val:
        with self.manager.transaction():
          self.manager.store().put(key, f.read())
          self.manager.build(n("html", key))

  def run(self, entry=None):
    with self.manager.transaction():
      if not self.checked_fs:
        self.check()

      if not self.config_imported:
        self.import_config()

      if entry is not None:
        key = n("file", entry)
      else:
        key = "index"
 
      self.manager.build(key)
