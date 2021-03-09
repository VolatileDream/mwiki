#!/usr/bin/env python3

import enum
from typing import Dict, Optional, final, ForwardRef

class Plugin:
  def name(self):
    """Name of the plugin.

    The Plugin is required to share it's name with the filename that contains
    it in ./plugins, this is for change detection convenience.
    """
    pass

  def has_meta(self):
    return hasattr(self, MetaPageMixin.render_metapage.__name__)

  def has_render(self):
    return hasattr(self, RenderMixin.get_content.__name__)

  def is_directive(self):
    return hasattr(self, DirectivePlugin.directives.__name__)

  def compute_partial_index(self, entry_name : str, entry_content : str) -> Optional[bytes]:
    """Called after an entry is changed, to update it's index part.

    Whatever gets returned is stored.
    """
    pass

  def aggregate_index(self, index_content : Dict[str, bytes]) -> bytes:
    """Called to update the index for MetaPageMixin and RenderMixin.

    Passed a dictionary that has all the return values from `compute_partial_index`.
    """
    pass


class MetaPageMixin:
  def render_metapage(self, index : bytes) -> str:
    """Using the index, generate the plugins meta-page."""
    pass


class RenderMixin:
  def get_content(self, entry_name : str, index : bytes) -> str:
    """Using the content from the index, generate render content."""
    pass


class DirectiveHandling(enum.Enum):
  """Specifies behaviour for Directives declared by a DirectivePlugin.

  DirectivePlugins are given coarse control over the date they would pull into
  their indexes. The options are to remove the content, or to leave it in the
  final page.
  """
  REMOVE = enum.auto()
  KEEP = enum.auto()


class DirectivePlugin(Plugin):
  """A special type of mwiki plugin.

  Plugins implementing this type are treated specially by mwiki, because they
  are not in control of their own index updates they are treated specially by
  the rendering engine.

  Instead of implementing `update_index` these plugins declare directives
  which are collected into the index, and optionally removed when rendering
  the entry later. These are the only plugins that are currently allowed to
  remove user content from pages before final render.
  """

  @final
  def update_index(self, name, content):
    keep = []
    prefixes = set(self.directives().keys())
    for line in content.split("\n"):
      for p in prefixes:
        if line.startswith(p):
          keep.append(line)
          break # only add to keep once.
    return "\n".join(keep)

  def directives(self) -> Dict[str, DirectiveHandling]:
    pass

  @staticmethod
  def rewrite_content(content, plugin: ForwardRef('DirectivePlugin')):
    removes = []
    for directive, handling in plugin.directives().items():
      if handling == DirectiveHandling.REMOVE:
        removes.append(directive)

    updated_lines = []
    for line in content.split("\n"):
      started = False
      for r in removes:
        if line.startswith(r):
          started = True
      if not started:
        updated_lines.append(line)

    return "\n".join(updated_lines)
