import sys
from python.interpreter import *
from python.interop import load_module

def init():
  global GLOBAL_ENV
  builtins = [ADD, SUB, EQ, IS_SYMBOL, CAR, CDR, CONS, EVAL, PRINT]
  frame = {}
  for symbol, fn in builtins:
    frame[symbol] = fn
  GLOBAL_ENV = (frame, ())
  load_module("src/core", GLOBAL_ENV)

def repl():
  while True:
    try:
      print(lispprint(eval(parse(input("> ")), GLOBAL_ENV)))
    except Exception as e:
      print(e)

if __name__ == "__main__":
  init()
  if len(sys.argv) == 2:
    load_module(sys.argv[1][:-4], GLOBAL_ENV)
  else:
    repl()
