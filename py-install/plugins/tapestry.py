
from collections import defaultdict
import json

from pymwiki.plugins import Plugin, DirectivePlugin, DirectiveHandling, RenderMixin

ALIAS = "!tapestry:alias"
MENTION = "!tapestry:mention"
ORDER = "!tapestry:order"

def maybe_title(title, content):
  if not content:
    return []
  return ["## " + title] + content


def render_event(thread, event, mentions):
  # Two options for mentioning a thread:
  #  * Only order directive appears (len(mentions) == 0)
  #  * Mentioned on a page
  if (thread in mentions and len(mentions) == 1) or len(mentions) == 0:
    return " * #" + event
  else:
    return " * #{} as @{}".format(event, ", @".join(mentions))


class TapestryPlugin(DirectivePlugin):
  def name(self):
    return "tapestry"

  def directives(self):
    return {
      ALIAS: DirectiveHandling.REMOVE,
      MENTION: DirectiveHandling.REMOVE,
      ORDER: DirectiveHandling.REMOVE,
    }

  def get_content(self, entry, index):
    index = json.loads(index)

    # output in two parts:
    # Ordering & alias on this page.
    # mentions to this page from elsewhere.

    # Process items in our page
    mentions = []
    aliases = []
    ordering = []
    for l in index[entry]:
      if l.startswith(ORDER):
        event = l[len(ORDER):].strip()
        ordering.append(event)
      if l.startswith(ALIAS):
        alias = l[len(ALIAS):].strip()
        aliases.append(alias)
      if l.startswith(MENTION):
        mention = l[len(MENTION):].strip()
        mentions.append(mention)

    alias_l = set(aliases)
    alias_l.add(entry)

    # Lookup other items to find mentions of this entry.
    events = defaultdict(set)
    for key, lines in index.items():
      for l in lines:
        if l.startswith(MENTION):
          mention = l[len(MENTION):].strip()
          if mention in alias_l:
            events[key].add(mention)

    # Output formatting:
    #  * Aliases
    #  * unoredered events
    #  * Oredered events
    #  * mentions
    #
    # Mentions is not expected to exist with other directives, but just in case
    # it is, we always process.

    unordered = set(events.keys()).difference(ordering)

    #print(aliases, alias_l, unordered, ordering, events)

    output = []
    output += maybe_title("Known Aliases", [" * @" + a for a in aliases])
    output += maybe_title("Unordered Events", [render_event(entry, e, events[e]) for e in unordered])
    output += maybe_title("Ordered Events", [render_event(entry, e, events[e]) for e in ordering])
    output += maybe_title("Tapestry Mentions", [" * @" + m for m in mentions])

    return "\n".join(output)

