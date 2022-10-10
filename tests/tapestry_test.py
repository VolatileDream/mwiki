import json
import unittest
import sys

try:
  from tapestry import TapestryPlugin
except:
  sys.path.insert(0, "./py-install/plugins/")
  from tapestry import TapestryPlugin
  sys.path.pop(0)


class TapestryTests(unittest.TestCase):
  def test_mentions(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": ["!tapestry:mention abc", "!tapestry:mention def"],
    })

    expect = "\n".join([
      "## Tapestry Mentions",
      " * @abc",
      " * @def",
    ])

    self.assertEqual(t.get_content("page", index), expect)

  def test_aliases(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": ["!tapestry:alias abc", "!tapestry:alias def"],
    })

    expect = "\n".join([
      "## Known Aliases",
      " * @abc",
      " * @def",
    ])

    self.assertEqual(t.get_content("page", index), expect)

  def test_no_aliases(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": [],
    })

    expect = "\n".join([])

    self.assertEqual(t.get_content("page", index), expect)

  def test_unordered_mention(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": [],
      "other-page": ["!tapestry:mention page"],
    })

    expect = "\n".join([
      "## Unordered Events",
      " * #other-page",
    ])

    self.assertEqual(t.get_content("page", index), expect)

  def test_ordered_mention(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": ["!tapestry:order other-page", "!tapestry:order third-page"],
      "other-page": ["!tapestry:mention page"],
      "third-page": ["!tapestry:mention page"],
    })

    expect = "\n".join([
      "## Ordered Events",
      " * #other-page",
      " * #third-page",
    ])

    self.assertEqual(t.get_content("page", index), expect)

  def test_mention_with_alias(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": ["!tapestry:alias hello"],
      "world": ["!tapestry:mention hello"],
    })

    expect = "\n".join([
      "## Known Aliases",
      " * @hello",
      "## Unordered Events",
      " * #world as @hello",
    ])

    self.assertEqual(t.get_content("page", index), expect)

  def test_ordered_mention_with_alias(self):
    t = TapestryPlugin()

    index = json.dumps({
      "page": [
          "!tapestry:order third-page",
          "!tapestry:alias hello",
          "!tapestry:order other-page",
          "!tapestry:order no-page",
      ],
      "world": ["!tapestry:mention hello"],
      "other-page": ["!tapestry:mention hello"],
      "third-page": ["!tapestry:mention page"],
    })

    expect = "\n".join([
      "## Known Aliases",
      " * @hello",
      "## Unordered Events",
      " * #world as @hello",
      "## Ordered Events",
      " * #third-page",
      " * #other-page as @hello",
      " * #no-page",
    ])

    self.assertEqual(t.get_content("page", index), expect)

