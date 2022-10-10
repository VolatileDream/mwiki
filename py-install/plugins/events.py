
from collections import defaultdict
import re

from pymwiki.plugins import Plugin, MetaPageMixin

DATE = re.compile("^[0-9]+-[0-9][0-9]-[0-9][0-9]$")
EVENT = re.compile("^([0-9]+-[0-9][0-9]-[0-9][0-9]) !(event|event-start|event-end) +(.+)$")

def date(string):
  return tuple([int(x) for x in string.split("-")])


def first(item):
  return item[0]


def date_fmt(year_padding):
  return "{{:0>{width}}}/{{:0>2}}/{{:0>2}}".format(width=year_padding)


# This could probably have been a DirectivePlugin
class EventsPlugin(Plugin, MetaPageMixin):
  def name(self):
    return "events"

  def compute_partial_index(self, name, content):
    if not DATE.fullmatch(name):
      return None

    event_lines = []
    for line in content.split("\n"):
      if line.startswith("!event"):
        event_lines.append(name + " " + line)

    return "\n".join(event_lines)

  def aggregate_index(self, index_dict):
    agg = []
    for key in index_dict:
      if index_dict[key]:
        agg.append(index_dict[key])

    return "\n".join(agg)

  def render_metapage(self, index):
    single_events = []
    paired_events = []

    lines = index.split("\n")
    for line in lines:
      if not line:
        continue
      date_str, event_type, event = EVENT.match(line).groups()
      d = date(date_str)

      if event_type == "event":
        single_events.append((d, event))
      else:
        paired_events.append((d, event_type, event))

    paired_events.sort(key=first)

    # event -> start dates
    unmatched = defaultdict(list)
    linearized = []

    while len(paired_events) > 0:
      d, event_type, event = paired_events.pop(0)
      if event_type == "event-end":
        if len(unmatched[event]) > 0:
          # TODO: should this really pop from the back?
          start = unmatched[event].pop()
          linearized.append((start, d, event))
        else:
          linearized.append((None, d, event))
      else:
        unmatched[event].append(d)

    for event in unmatched:
      for d in unmatched[event]:
        linearized.append((d, None, event))

    largest_date = max(
                      max(filter(bool, map(first, single_events)), default=(0,0,0)),
                      max(filter(bool, map(first, linearized)), default=(0,0,0)))

    # this is so terrible, but it's an easy way to find numerical width.
    pad_width = len(str(first(largest_date)))
    fmt = date_fmt(pad_width)

    all_events = []
    for d, event in single_events:
      date_str = fmt.format(*d)
      all_events.append(" - {} {}".format(date_str, event))
    for start, end, event in linearized:
      if start:
        start_str = fmt.format(*start)
      else:
        start_str = "*"
      if end:
        end_str = fmt.format(*end)
      else:
        end_str = "~"
      all_events.append(" - {}-{} {}".format(start_str, end_str, event))

    all_events.sort()

    return "# Events\n---\n" + "\n".join(all_events)

