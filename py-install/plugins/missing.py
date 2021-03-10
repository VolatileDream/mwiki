
import re

from pymwiki.plugins import Plugin, MetaPageMixin

LINK = re.compile("[#@]([a-zA-Z0-9~_-]+)")

# this looks a lot like the Mentions plugin, but we use a different format
# for storage. This is because we need to know about empty pages.

class MissingPlugin(Plugin, MetaPageMixin):
  def name(self):
    return "missing"

  def compute_partial_index(self, name, content):
    links = set(LINK.findall(content))
    lines = ["#" + name] + list(links)

    return "\n".join(lines)

  def aggregate_index(self, index_dict):
    agg = []
    for key in index_dict:
      agg.append(index_dict[key])

    return "\n".join(agg)

  def render_metapage(self, index):
    lines = index.split("\n")

    # page -> links out
    mentions = {}

    key = None
    for l in lines:
      if l.startswith("#"):
        key = l[1:]
        if key not in mentions:
          mentions[key] = set()
      else:
        mentions[key].add(l)

    # page -> links in
    missing = {}
    for key in mentions:
      links = mentions[key]
      for l in links:
        if l not in missing:
          missing[l] = set()
        missing[l].add(key)

    for key in mentions:
      # these pages exist
      if key in missing:
        del missing[key]

    output = ["# ~missing"]
    for key in missing:
      output.append(key)
      for incoming in missing[key]:
        output.append("&nbsp;#{}".format(incoming))

    return "\n".join(output)



