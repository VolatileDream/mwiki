import unittest
import sqlite3
from src.plugins import DirectivePlugin, DirectiveHandling

class SimpleDirective(DirectivePlugin):
  def directives(self):
    return {
      "!abc": DirectiveHandling.REMOVE,
      "!def": DirectiveHandling.REMOVE,
      "!ghi": DirectiveHandling.KEEP,
    }

class PluginTests(unittest.TestCase):

  def test_directive_rewrite(self):
    content = "!abc hi\n!def hello\n!ghi stuff\nsimple line\n"
    new_content = DirectivePlugin.rewrite_content(content, SimpleDirective())

    self.assertEqual(new_content, "!ghi stuff\nsimple line\n")
