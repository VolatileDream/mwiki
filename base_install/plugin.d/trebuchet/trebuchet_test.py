#!/usr/bin/env python3

from trebuchet import TrebuchetFactory, Trebuchet, TrebuchetApp

def correct_parse(string):
  return (
    TrebuchetFactory()
      .with_glyph("[x]")
      .with_glyph("[/]")
      .with_glyph("[]")
      .with_glyph("*")
      .with_glyph("---", has_indent=False)
      .create_from(string=string))

def fail_parse(string):
  try:
    (TrebuchetFactory()
      .with_glyph("*")
      .with_glyph("---", has_indent=False)
      .create_from(string=string))
  except Exception as e:
    print(e)

if __name__ == "__main__":

  catapult=(correct_parse("""
                * abc
                  * abc 1
                  * abc 2

                [] def
                  [x] def 1
                  [] def 2

                [x] ghi
                  * ghi 1
                [/] jkl
                  * jkl 1
                  [x] jkl 2
               ---
               """))
  print(catapult.str())
  print("###")
  print(catapult.reorder(["*", "[]", "---", "[/]", "[x]"]).str())
  print("###")
  print(catapult
      .reorder(["*", "[]", "---", "[/]", "[x]"])
      .filter(lambda glyph: glyph not in ["[x]", "[/]"])
      .str())
  print("###")
  print(TrebuchetApp(catapult, ["*"], ["[]"], ["[/]", "[x]"]).advance_tree(catapult).str())
  print("###")
  fail_parse(
    """
    * hello
    - world
    """)
