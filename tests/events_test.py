import unittest
import sys

try:
  from events import EventsPlugin
except:
  sys.path.insert(0, "./py-install/plugins/")
  from events import EventsPlugin
  sys.path.pop(0)


class EventTests(unittest.TestCase):
  def test_name_match(self):
    e = EventsPlugin()
    self.assertEqual(e.compute_partial_index("abc", "!event def"), None)

  def test_extraction(self):
    e = EventsPlugin()

    self.assertEqual(e.compute_partial_index("2020-10-10", "hello world"), '')
    self.assertEqual(e.compute_partial_index("2020-10-10", "!event def"), "2020-10-10 !event def")
    self.assertEqual(e.compute_partial_index("2020-10-10", "!event-start def"), "2020-10-10 !event-start def")
    self.assertEqual(e.compute_partial_index("2020-10-10", "!event-end def"), "2020-10-10 !event-end def")

  def test_single_events(self):
    events = [
      "2020-10-11 !event hello",
      "2020-10-10 !event def",
      "2020-11-11 !event world",
    ]

    expect = [
      "# Events",
      "---",
      " - 2020/10/10 def",
      " - 2020/10/11 hello",
      " - 2020/11/11 world",
    ]

    self.assertEqual(EventsPlugin().render_metapage("\n".join(events)), "\n".join(expect))

  def test_start_end(self):
    events = [
      "2020-11-10 !event-end hello",
      "2020-10-11 !event-start hello",
    ]

    expect = [
      "# Events",
      "---",
      " - 2020/10/11-2020/11/10 hello",
    ]

    self.assertEqual(EventsPlugin().render_metapage("\n".join(events)), "\n".join(expect))

  def test_matching_start_end(self):
    # Does this behaviour even make sense?
    events = [
      "2020-01-11 !event-start hello",
      "2020-02-11 !event-start hello",
      "2020-03-11 !event-end hello",
      "2020-04-11 !event-end hello",
    ]

    # Notice the interleave, like matching parens.
    expect = [
      "# Events",
      "---",
      " - 2020/01/11-2020/04/11 hello",
      " - 2020/02/11-2020/03/11 hello",
    ]

    self.assertEqual(EventsPlugin().render_metapage("\n".join(events)), "\n".join(expect))

  def test_mismatched(self):
    events = [
      "2020-01-11 !event-start hello",
      "2020-04-11 !event-end world",
    ]

    expect = [
      "# Events",
      "---",
      " - *-2020/04/11 world",
      " - 2020/01/11-~ hello",
    ]

    self.assertEqual(EventsPlugin().render_metapage("\n".join(events)), "\n".join(expect))
