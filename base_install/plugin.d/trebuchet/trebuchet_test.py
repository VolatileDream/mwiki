#!/usr/bin/env python3

import sys
from trebuchet import Trebuchet, TrebuchetApp, TrebuchetConfig, TrebuchetParser

CONFIG = TrebuchetConfig(["#", "*", "[]", "---", "[/]", "[x]"], ["[/]", "[x]"], "---", {"rocks.daily": "%Y-%m-%d"})

def correct_parse(string):
  return TrebuchetParser(CONFIG).create_from(string=string)

def fail_parse(string):
  try:
    TrebuchetParser(TrebuchetConfig(["*", "---"], [], "---")).create_from(string=string)
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
  print(catapult.reorder().str())
  print("###")
  print(catapult
      .reorder()
      .filter(lambda glyph: glyph not in ["[x]", "[/]"])
      .str())
  print("###")
  fail_parse(
    """
    * hello
    - world
    """)
  print("###")

  cfg = TrebuchetConfig.from_ini("config.ini")
  app = TrebuchetApp(cfg)
  print(app.load_rock("rocks.daily").str())