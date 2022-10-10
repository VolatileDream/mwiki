import unittest
from pymwiki.template import Template

class TemplateTests(unittest.TestCase):
  def test_no_vars(self):
    t = Template.parse("abc")
    self.assertEqual(t.variables(), frozenset())

    self.assertEqual(t.render(), "abc")

  def test_open_var(self):
    with self.assertRaises(Exception):
      Template.parse("abc {{")

    with self.assertRaises(Exception):
      Template.parse("abc }}")

  def test_empty_var(self):
    with self.assertRaises(Exception):
      Template.parse("{{  }}")

  def test_vars_stripped(self):
    t = Template.parse("{{ abc }}")
    self.assertEqual(t.variables(), frozenset(["abc"]))

  def test_missing_bindings(self):
    t = Template.parse("abc {{ 123 }} def")

    with self.assertRaises(Exception):
      t.render()

  def test_render(self):
    t = Template.parse("abc {{ ghi }} def")

    self.assertEqual(t.render(ghi="123"), "abc 123 def")
