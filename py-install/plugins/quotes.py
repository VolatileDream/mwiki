
import json
from pymwiki.plugins import DirectivePlugin, DirectiveHandling, MetaPageMixin

class QuotesPlugin(DirectivePlugin, MetaPageMixin):
  def name(self):
    return "quotes"

  def directives(self):
    return {
      "!quotes": DirectiveHandling.KEEP,
    }

  def render_metapage(self, index):
    index_dict = json.loads(index)
    ordering = list(index_dict)
    ordering.sort(key=lambda x: x.upper())

    out = [
      "# ~quotes",
      "---------",
    ]
    for key in ordering:
      quotes = index_dict[key]
      for q in quotes:
        if not q:
          continue
        q = q + " \\n #" + key
        q = q.replace("!quotes", "", 1).strip().replace("\\n", "\n&nbsp;&nbsp;")
        out.append("") # extra empty line to separate quotes.
        out.append(q)

    return "\n".join(out)


