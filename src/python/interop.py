from python.interpreter import read, lexan, eval
import os

def load_module(modulename, env):
  filename = "%s.ebh" % modulename
  fin = open(filename, 'r')
  contents = fin.read()
  fin.close()
  tokens = lexan(contents)
  while len(tokens) > 0:
    eval(read(tokens), env)
