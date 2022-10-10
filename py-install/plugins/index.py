

import pymwiki.plugins
import re

DATE = re.compile("^....-..-..$")
GEN = re.compile("^~")

class IndexRender(pymwiki.plugins.Plugin, pymwiki.plugins.RenderMixin):
  def name(self):
    return "index"

  @staticmethod
  def link(entry):
    return "<a href='{name}.html'>{name}</a>".format(name=entry)

  @staticmethod
  def section(entries, name, matcher):
    "Generate the section if it has entries"
    matching = list(filter(matcher, entries))
    matching.sort(key=lambda x: x.upper())
    if matching:
      return ["<h1>{}</h1><hr/>".format(name)] + [IndexRender.link(entry) for entry in matching]
    else:
      return []

  def get_content(self, entry, entries):
    journal = IndexRender.section(entries, "Journal", lambda x: DATE.match(x))
    journal.reverse()
    wiki = IndexRender.section(entries, "Wiki", lambda x: not DATE.match(x) and not GEN.match(x))
    gen = IndexRender.section(entries, "Generated Pages", lambda x: GEN.match(x))

    return "<br>\n".join(journal + wiki + gen)
