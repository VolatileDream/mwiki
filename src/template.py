#!/usr/bin/env python3

class Template:
  @staticmethod
  def parse(string):
    START = "{{"
    END = "}}"

    index = 0
    text = []
    variables = []

    while index < len(string):
      # This is always okay for well formatted strings.
      # Templates can't be nested, and must always appear in order.
      v_start = string.find(START, index)
      v_end = string.find(END, index)

      if v_start == -1 and v_end == -1:
        break

      if v_end < v_start or v_start == -1:
        raise Exception("Mismatched {} and {} at indexes: {}, {}".format(START, END, v_end, v_start))

      text.append(string[index:v_start])

      var = string[v_start + len(START):v_end].strip()
      if not var:
        raise Exception("Empty variable at index {}".format(v_start))
      variables.append(var)

      index = v_end + len(END)

    if index < len(string):
      text.append(string[index:])

    return Template(text, variables)

  def __init__(self, text, variables):
    if len(text) > len(variables) + 1:
      raise Exception("Unbalanced Text and Variable declarations! {} vs {}".format(len(text), len(variables)))
    self.text = text
    self.var = variables
    self.unique_vars = frozenset(self.var)
    
  def variables(self):
    return self.unique_vars

  def render(self, **bindings):
    # Check that we have all the bindings.
    unbound = self.unique_vars.difference(bindings.keys())
    if unbound:
      raise Exception("Not all variables bound, did not find: {}".format(", ".join(unbound)))

    segments = []
    for text, var in zip(self.text, self.var):
      segments.append(text)
      segments.append(bindings[var])

    if len(self.text) > len(self.var):
      # extra text segment after the last variable.
      segments.append(self.text[-1])

    return "".join(segments)
