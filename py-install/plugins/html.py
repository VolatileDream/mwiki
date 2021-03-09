

import pymwiki.plugins
import re

def sed(match, replace, iterable):
  p = re.compile(match)
  for i in iterable:
    yield p.sub(replace, i)

def start_spacing(line):
  start_tags = ["<h1>", "<h4>", "<hr/>"]
  for t in start_tags:
    if line.endswith(t):
      return True
  return False

def end_spacing(line):
  end_tags = ["</h1>", "</h4>", "<hr/>"]
  for t in end_tags:
    if line.startswith(t):
      return True

  return False

def join_lines(iterable):
  # We don't do "\n".join(line) because 
  # <h*> and <hr> tags add extra spacing,
  # so we stitch lines together a little differently.
  text = []
  for line in iterable:
    last = ""
    if len(text) > 0:
      last = text[-1]

    if end_spacing(last) or start_spacing(line):
      new_line = last + line
      if len(text) > 0:
        text.pop()  # remove because it was merged into new_line
      text.append(new_line)
    else:
      text.append(line)

  return "<br>\n".join(text)


class HtmlRender(pymwiki.plugins.Plugin, pymwiki.plugins.RenderMixin):

  SWAPS = [
    ("<", "&lt;"),
    (">", "&gt;"),
    ("^# (.+)$", "<h1>\\1</h1>"),
    ("^##+ (.+)$", "<h4>\\1</h4>"),
    ("([#@]([a-zA-Z0-9~-]+))", '<a href="\\2.html">\\1</a>'),
    ("^(\\[([^\\]+])\\]:)",'<span id="LINK-\\2">\\1</span>'),
    ("(\\[([^\\]+])\\])",'<a href="#LINK-\\2">\\1</a>'),
    ("^---+$", "<hr/>"),
  ]

  def name(self):
    return "html"

  def get_content(self, entry, content):
    lines = content.split("\n")
    for m, r in HtmlRender.SWAPS:
      lines = sed(m,r, lines)
    return join_lines(lines)

