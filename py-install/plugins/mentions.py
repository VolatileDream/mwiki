
import re

from pymwiki.plugins import Plugin, RenderMixin

LINK = re.compile("[#@]([a-zA-Z0-9~_-]+)")
LINE_TEMPLATE = "{} :: {}"
REMOVAL = LINE_TEMPLATE.format("", "")

class MentionsPlugin(Plugin, RenderMixin):
  def name(self):
    return "mentions"

  def compute_partial_index(self, name, content):
    links = set(LINK.findall(content))
    lines = []
    for l in links:
      lines.append(LINE_TEMPLATE.format(l, name))

    return "\n".join(lines)

  def aggregate_index(self, index_dict):
    agg = []
    for key in index_dict:
      agg.append(index_dict[key])

    return "\n".join(agg)

  def get_content(self, entry, index):
    lines = index.split("\n")

    prefix = LINE_TEMPLATE.format(entry, "")

    output = []
    for l in lines:
      if l.startswith(prefix):
        mention = l[l.index(REMOVAL) + len(REMOVAL):]
        output.append("#" + mention)

    if output:
      output.insert(0, "## Mentions")

    return "\n".join(output)



