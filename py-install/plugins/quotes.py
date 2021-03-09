#Quotes plugin can be implemented several ways:

class QuotesPlugin1(Plugin, MetaPagePluginMixin):
  def name(self):
    return "quotes"

  def update_index(self, name, content):
    lines = []
    for line in content.split("\n"):
      if line.startswith("!quotes"):
        l = line.replace("!quotes", "", count=1).strip()
        lines.append(l)
    return "\n".join(lines)

  def render_metapage(self, index_dict):
    ordering = list(index_dict)
    ordering.sort(key=lambda x: x.upper())

    out = [
      "# ~quotes",
      "---------",
    ]
    for key in order:
      quotes = index_dict[key].split("\n")
      for q in quotes:
        q = q.replace("\\n", "\n&nbsp;&nbsp;")
        out.append("") # extra empty line to separate quotes.
        out.append(q)

    return "\n".join(out)

class QuotesPlugin2(DirectivePlugin, MetaPagePluginMixin):
  def directives(self):
    return {
      "!quotes": DirectiveHandling.KEEP,
    }

  def render_metapage(self, index_dict):
    ordering = list(index_dict)
    ordering.sort(key=lambda x: x.upper())

    out = [
      "# ~quotes",
      "---------",
    ]
    for key in order:
      quotes = index_dict[key].split("\n")
      for q in quotes:
        q = q.replace("!quotes", "", 1).strip().replace("\\n", "\n&nbsp;&nbsp;")
        out.append("") # extra empty line to separate quotes.
        out.append(q)

    return "\n".join(out)


class QuotesPlugin3(DirectivePlugin, MetaPagePluginMixin, RenderPluginMixin):
  def directives(self):
    return {
      "!quotes": DirectiveHandling.REMOVE,
    }

  def __quote(self, q):
    return q.replace("!quotes", "", 1).strip().replace("\\n", "\n&nbsp;&nbsp;")

  # By implementing this function, we surrender placement of the quotes to the
  # mwiki Render engine, and whatever the user has input for the template.
  def get_content(self, name, content):
    out = []
    quotes = content[name].split("\n")
    for q in quotes:
      out.append(self.__quote(q))

    return "\n".join(out)

  def render_metapage(self, index_dict):
    ordering = list(index_dict)
    ordering.sort(key=lambda x: x.upper())

    out = [
      "# ~quotes",
      "---------",
    ]
    for key in order:
      quotes = index_dict[key].split("\n")
      for q in quotes:
        out.append("") # extra empty line to separate quotes.
        out.append(self.__quote(q))

    return "\n".join(out)
    
