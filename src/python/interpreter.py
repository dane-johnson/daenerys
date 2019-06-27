import operator as op
from types import LambdaType, new_class
import builtins
py_eval = eval

def cons (a, b):
  return (a,) + b
def car(a):
  return a[0]
def cdr(a):
  return a[1:]
def caar(a):
  return car(car(a))
def cadr(a):
  return car(cdr(a))
def cdar(a):
  return cdr(car(a))
def cddr(a):
  return cdr(cdr(a))
def caaar(a):
  return car(caar(a))
def caadr(a):
  return car(cadr(a))
def cadar(a):
  return car(cdar(a))
def caddr(a):
  return car(cddr(a))
def cdaar(a):
  return cdr(caar(a))
def cdadr(a):
  return cdr(cadr(a))
def cddar(a):
  return cdr(cdar(a))
def cdddr(a):
  return cdr(cddr(a))

class Symbol:
  def __init__(self, symbol):
    self.symbol = symbol
  def __eq__(self, o):
    return isinstance(o, Symbol) and self.symbol == o.symbol
  def __cmp__(self, o):
    return cmp(hash(self), hash(o))
  def __hash__(self):
    return hash(self.symbol)
  def __repr__(self):
    return "<symbol %s>" % self.symbol

class Keyword:
  def __init__(self, keyword):
    self.keyword = keyword
  def __eq__(self, o):
    return isinstance(o, Keyword) and self.keyword == o.keyword
  def __cmp__(self, o):
    return cmp(hash(self), hash(o))
  def __hash__(self):
    return hash(self.keyword)
  def __repr__(self):
    return ":%s" % self.keyword

class Macro:
  def __init__(self, params, expression):
    self.params = params
    self.expression = expression
    self.__name__ = '<macro>'
  def expand(self, args, env):
    return eval(self.expression, extend_environment(self.params, args, env))
  def __call__(self, args, env):
    return eval(self.expand(args, env), env)

## Native symbols
QUOTE = Symbol('quote')
QUASIQUOTE = Symbol('quasiquote')
UNQUOTE = Symbol('unquote')
MACROEXPAND = Symbol('macroexpand')
IF = Symbol('if')
FN = Symbol('fn')
DEF = Symbol('def')
LIST = Symbol('list')
LET = Symbol('let')
MACRO = Symbol('macro')
DOT = Symbol('.')
NEW = Symbol('new')
APPLY = Symbol('apply')
IMPORT = Symbol('import')

def eat_whitespace(prgm, i):
  while i < len(prgm) and prgm[i] in frozenset(" \n\t"):
    i += 1
  return i

def is_delimiter(prgm, i):
  return i >= len(prgm) or prgm[i] in frozenset("(){}[] \t\n")

def lexan(prgm):
  tokens = []
  i = 0
  while i < len(prgm):
    i = eat_whitespace(prgm, i)
    if i == len(prgm):
      break
    char = prgm[i]
    if char in frozenset("':`~#(){}[]"):
      tokens.append(char)
      i += 1
    elif char == '"':
      j = i + 1
      while prgm[j] != '"':
        if prgm[j] == "\\":
          j += 1
        j += 1
      tokens.append('"' + prgm[i+1:j] + '"')
      i = j + 1
    elif char in frozenset("0123456789"):
      j = i + 1
      while not is_delimiter(prgm, j):
        j += 1
      tokens.append(float(prgm[i:j]))
      i = j
    else:
      j = i + 1
      while not is_delimiter(prgm, j):
        j += 1
      tokens.append(prgm[i:j])
      i = j
  return tokens

def read(tokens):
  token = tokens.pop(0)
  if token == ')':
    raise RuntimeError("Unbalanced parenthesis")
  if token == '}':
    raise RuntimeError("Unbalanced curlies")
  if token == '(':
    return readlist(tokens)
  if token == '{':
    return readdict(tokens)
  if token == "'":
    return cons(QUOTE, cons(read(tokens), ()))
  if token == "`":
    return cons(QUASIQUOTE, cons(read(tokens), ()))
  if token == "~":
    return cons(UNQUOTE, cons(read(tokens), ()))
  if token == ':':
    return Keyword(tokens.pop(0))
  if isinstance(token, str):
    if token[0] == '"':
      return token[1:-1]
    if token == 'True':
      return True
    if token == 'False':
      return False
    if token == 'nil':
      return ()
    return Symbol(token)
  return token

def readlist(tokens):
  token = tokens.pop(0)
  if token == ")":
    return ()
  else:
    tokens.insert(0, token)
    return cons(read(tokens), readlist(tokens))

def readdict(tokens):
  token = tokens.pop(0)
  if token == "}":
    return {}
  else:
    tokens.insert(0, token)
    key = read(tokens)
    val = read(tokens)
    mydict = readdict(tokens)
    mydict[key] = val
    return mydict

def parse(prgm):
  return read(lexan(prgm))

def is_self_evaluating(exp):
  return \
    isinstance(exp, str) or \
    isinstance(exp, float) or \
    isinstance(exp, Keyword) or \
    isinstance(exp, bool) or \
    isinstance(exp, int) or \
    is_nil(exp)

def is_symbol(exp):
  return isinstance(exp, Symbol)

def is_nil(exp):
  return isinstance(exp, tuple) and exp == ()

def is_lambda(exp):
  return isinstance(exp, LambdaType)

def is_macro(exp):
  return isinstance(exp, Macro)

def is_dict(exp):
  return isinstance(exp, dict)

def is_keyword(exp):
  return isinstance(exp, Keyword)

def is_cons(exp):
  return isinstance(exp, tuple)

def is_list(exp):
  return is_nil(exp) or is_cons(exp) and is_list(cdr(exp))

def is_falsy(exp):
  return not exp or is_nil(exp) or exp == False

def lookup(symbol, env):
  if is_nil(env):
    raise LookupError("Could not find %s" % symbol)
  else:
    frame = car(env)
    if symbol in frame:
      return frame[symbol]
    return lookup(symbol, cdr(env))

def eval(exp, env):
  if is_self_evaluating(exp):
    return exp
  if is_symbol(exp):
    return lookup(exp, env)
  if is_dict(exp):
    return evaldict(exp, env)
  if is_list(exp):
    if car(exp) == QUOTE:
      return cadr(exp)
    if car(exp) == QUASIQUOTE:
      return evalquasi(cadr(exp), env)
    if car(exp) == IF:
      if not is_falsy(eval(cadr(exp), env)):
        return eval(caddr(exp), env)
      if is_nil(cdddr(exp)):
        return () 
      return eval(car(cdddr(exp)), env)
    if car(exp) == LIST:
      return evallist(cdr(exp), env)
    if car(exp) == FN:
      params = cadr(exp)
      expression = caddr(exp)
      fn = lambda args: eval(expression, extend_environment(params, args, env))
      return fn
    if car(exp) == MACRO:
      params = cadr(exp)
      expression = caddr(exp)
      return Macro(params, expression)
    if car(exp) == DOT:
      pyobject = eval(cadr(exp), env)
      method = caddr(exp)
      ops = evallist(cdddr(exp), env)
      return wrap_python_fn(getattr(pyobject, method.symbol))(ops)
    if car(exp) == NEW:
      classname = cadr(exp)
      args = evallist(cddr(exp), env)
      return wrap_python_fn(getattr(builtins, classname.symbol))(args)
    if car(exp) == IMPORT:
      define_variable(cadr(exp), __import__(cadr(exp).symbol), env)
      return ()
    if car(exp) == DEF:
      define_variable(cadr(exp), eval(caddr(exp), env), env)
      return ()
    if car(exp) == APPLY:
      return eval(cadr(exp), env)(eval(caddr(exp), env))
    if is_lambda(car(exp)):
      return car(exp)(evallist(cdr(exp), env))
    if is_macro(car(exp)):
      return car(exp)(cdr(exp), env)
    if is_dict(car(exp)):
      return eval(car(exp), env)[eval(cadr(exp), env)]
    if is_keyword(car(exp)):
      return eval(cadr(exp), env)[car(exp)]
  return eval(cons(eval(car(exp), env), cdr(exp)), env)

def evallist(exp, env):
  if is_nil(exp):
    return exp
  return cons(eval(car(exp), env), evallist(cdr(exp), env))

def evaldict(exp, env):
  newdict = {}
  for key in exp:
    newkey = eval(key, env)
    newval = eval(exp[key], env)
    newdict[newkey] = newval
  return newdict

def evalquasi(exp, env):
  if is_nil(exp):
    return exp
  if is_list(exp):
    if car(exp) == UNQUOTE:
      return eval(cadr(exp), env)
    return cons(evalquasi(car(exp), env), evalquasi(cdr(exp), env))
  return exp

def extend_environment(vars, vals, env):
  frame = {}
  for var, val in zip(vars, vals):
    frame[var] = val
  return cons(frame, env)

def define_variable(var, val, env):
  frame = car(env)
  frame[var] = val
  if is_lambda(val):
    val.__name__ = "<fn %s>" % var.symbol

def lispprint(exp):
  if is_self_evaluating(exp):
    return repr(exp)
  if is_symbol(exp):
    return exp.symbol
  if is_list(exp):
    return "(%s)" % lispprint_list(exp)
  if is_cons(exp):
    return "(%s . %s)" % (lispprint(car(exp)), lispprint(cdr(exp)))
  if is_lambda(exp) or is_macro(exp):
    return exp.__name__
  if is_dict(exp):
    return "{%s}" % lispprint_dict(exp)

def lispprint_list(exp):
  return " ".join(map(lispprint, exp))

def lispprint_dict(exp):
  return " ".join(map(lambda x: "%s %s" % (lispprint(x[0]), lispprint(x[1])), zip(exp.keys(), exp.values())))
  
## Builtin operations

def wrap_python_fn(fn):
  return lambda args: fn(*args)

def make_builtin(name, py_fn):
  symbol = Symbol(name)
  fn = wrap_python_fn(py_fn)
  fn.__name__ = "<builtin fn %s>" % name
  return symbol, fn

IS_SYMBOL = make_builtin('symbol?', is_symbol)
PRINT = make_builtin('print', lambda x: print(lispprint(x)))
CONS = make_builtin('cons', cons)
CAR = make_builtin('car', car)
CDR = make_builtin('cdr', cdr)
ADD = make_builtin("+", op.add)
SUB = make_builtin("-", op.sub)
EQ = make_builtin("=", op.eq)
EVAL = make_builtin("eval", eval)
