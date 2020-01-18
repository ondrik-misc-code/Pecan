#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir.base import *

class PralineTerm(IRNode):
    def __init__(self):
        super().__init__()
        self.evaluated_value = None

    def is_bool(self):
        return False

    def is_int(self):
        return False

    def is_string(self):
        return False

    # TODO: This function and the whole type system really ought to be improved
    def typeof(self):
        if self.is_bool():
            return "bool"
        elif self.is_int():
            return "int"
        elif self.is_string():
            return "string"
        else:
            return "unknown"

    def display(self):
        return repr(self)

class PralineDisplay(IRNode):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def evaluate(self, prog):
        prog.enter_praline_env()
        print(self.term.evaluate(prog).display())
        prog.exit_praline_env()

    def transform(self, transformer):
        return transformer.transform_PralineDisplay(self)

    def __repr__(self):
        return 'Display {} .'.format(self.term)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.term == other.term

    def __hash__(self):
        return hash(self.term)

class PralineExecute(IRNode):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def evaluate(self, prog):
        prog.enter_praline_env()
        self.term.evaluate(prog)
        prog.exit_praline_env()

    def transform(self, transformer):
        return transformer.transform_PralineExecute(self)

    def __repr__(self):
        return 'Execute {} .'.format(self.term)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.term == other.term

    def __hash__(self):
        return hash(self.term)

class PralineDef(IRNode):
    def __init__(self, name, args, body):
        super().__init__()
        self.name = name
        self.args = args
        self.body = body

    def evaluate(self, prog):
        if len(self.args) == 0:
            res = self.body
        else:
            res = Closure({}, self.args, self.body)
        prog.praline_define(self.name.var_name, res)

    def transform(self, transformer):
        return transformer.transform_PralineDef(self)

    def __repr__(self):
        return 'Define {} {} := {} .'.format(self.name, self.args, self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.name == other.name and self.args == other.args and self.body == other.body

    def __hash__(self):
        return hash((self.name, self.args, self.body))

class PralineCompose(PralineTerm):
    def __init__(self, f, g):
        super().__init__()
        self.f = f
        self.g = g

    def transform(self, transformer):
        return transformer.transform_PralineCompose(self)

    def __repr__(self):
        return '({} ∘ {})'.format(self.f, self.g)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.f == other.f and self.g == other.g

    def __hash__(self):
        return hash((self.f, self.g))

    def evaluate(self, prog):
        return PralineCompose(self.f.evaluate(prog), self.g.evaluate(prog))

    def apply(self, prog, arg):
        return self.f.evaluate(prog).apply(prog, self.g.evaluate(prog).apply(prog, arg))

class PralineVar(PralineTerm):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        return prog.praline_lookup(self.var_name)

    def transform(self, transformer):
        return transformer.transform_PralineVar(self)

    def __repr__(self):
        return '{}'.format(self.var_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var_name == other.var_name

    def __hash__(self):
        return hash((self.var_name))

class PralineApp(PralineTerm):
    def __init__(self, receiver, arg):
        super().__init__()
        self.receiver = receiver
        self.arg = arg

    def evaluate(self, prog):
        return self.receiver.evaluate(prog).apply(prog, self.arg.evaluate(prog)).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_PralineApp(self)

    def __repr__(self):
        return '({} {})'.format(self.receiver, self.arg)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.receiver == other.receiver and self.arg == other.arg

    def __hash__(self):
        return hash((self.receiver, self.arg))

class PralineBinaryOp(PralineTerm):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a and self.b == other.b

    def __hash__(self):
        return hash((self.a, self.b))

class PralineAdd(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineAdd(self)

    def __repr__(self):
        return '({} + {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() + eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineDiv(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineDiv(self)

    def __repr__(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() / eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineSub(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineSub(self)

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() - eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineMul(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineMul(self)

    def __repr__(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value() * eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineExponent(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineExponent(self)

    def __repr__(self):
        return '({} ^ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineInt(eval_a.get_value()**eval_b.get_value())
        elif eval_a.is_string() and eval_b.is_string():
            return PralineString(eval_a.get_value() + eval_b.get_value()) # + is for string concatenation
        else:
            raise TypeError('Both operands should be integers or strings in "{}", but they are {} and {}, respectively.'.format(self, eval_a.typeof(), eval_b.typeof()))

class PralineUnaryOp(PralineTerm):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.a == other.a

    def __hash__(self):
        return hash((self.a))

class PralineNeg(PralineUnaryOp):
    def __init__(self, a):
        super().__init__(a)

    def transform(self, transformer):
        return transformer.transform_PralineNeg(self)

    def __repr__(self):
        return '(-{})'.format(self.a)

    def evaluate(self, prog):
        temp = self.a.evaluate(prog)

        if not temp.is_int():
            raise TypeError('operand should evaluate to an integer in "{}"'.format(temp, self))

        return PralineInt(-temp.get_value())

class PralineList(PralineBinaryOp):
    def __init__(self, head, tail):
        super().__init__(head, tail)

    def transform(self, transformer):
        return transformer.transform_PralineList(self)

    def __repr__(self):
        if self.a is None:
            return '[]'
        else:
            return '({} :: {})'.format(self.a, self.b)

    def display(self):
        elems = []
        cur = self

        while cur.a is not None:
            elems.append(cur.a)
            cur = cur.b

        return '[{}]'.format(','.join([e.display() for e in elems]))

    def evaluate(self, prog):
        if self.a is not None:
            new_a = self.a.evaluate(prog)
        else:
            new_a = None

        if self.b is not None:
            new_b = self.b.evaluate(prog)
        else:
            new_b = None

        return PralineList(new_a, new_b)

class PralineMatch(PralineTerm):
    def __init__(self, t, arms):
        super().__init__()
        self.t = t
        self.arms = arms

    def transform(self, transformer):
        return transformer.transform_PralineMatch(self)

    def __repr__(self):
        return 'match {} with\n{}\nend'.format(self.t, '\n'.join(map(repr, self.arms)))

    def evaluate(self, prog):
        eval_t = self.t.evaluate(prog)

        for arm in self.arms:
            match_env = arm.match(eval_t)

            if match_env is not None:
                prog.praline_local_define_all(match_env)
                result = arm.expr.evaluate(prog)
                prog.praline_local_cleanup(match_env.keys())
                return result

        raise Exception('Inexhaustive match arms in "{}" (got "{}")'.format(self, eval_t))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.t == other.t and self.arms == other.arms

    def __hash__(self):
        return hash((self.t, self.arms))

class PralineMatchArm(IRNode):
    def __init__(self, pat, expr):
        super().__init__()
        self.pat = pat
        self.expr = expr

    def match(self, term):
        return self.pat.match(term)

    def transform(self, transformer):
        return transformer.transform_PralineMatchArm(self)

    def __repr__(self):
        return 'case {} => {}'.format(self.pat, self.expr)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.pat == other.pat and self.expr == other.expr

    def __hash__(self):
        return hash((self.pat, self.expr))

class PralineMatchPat(IRNode):
    def __init__(self):
        super().__init__()

class PralineMatchInt(PralineMatchPat):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def match(self, term):
        if term.is_int() and term.get_value() == self.val:
            return {}
        else:
            return None

    def transform(self, transformer):
        return transformer.transform_PralineMatchInt(self)

    def __repr__(self):
        return 'PralineMatchInt({})'.format(self.val)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.val))

class PralineMatchString(PralineMatchPat):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def match(self, term):
        if term.is_string() and term.get_value() == self.val:
            return {}
        else:
            return None

    def transform(self, transformer):
        return transformer.transform_PralineMatchString(self)

    def __repr__(self):
        return 'PralineMatchString({})'.format(self.val)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.val))

class PralineMatchList(PralineMatchPat):
    def __init__(self, head, tail):
        super().__init__()
        self.head = head
        self.tail = tail

    def match(self, term):
        if not type(term) is PralineList:
            return None

        if self.head is None or term.a is None:
            if self.head is None and term.a is None:
                return {}
            else:
                return None

        head_match_env = self.head.match(term.a)
        tail_match_env = self.tail.match(term.b)

        head_match_env.update(tail_match_env)

        return head_match_env

    def transform(self, transformer):
        return transformer.transform_PralineMatchList(self)

    def __repr__(self):
        return 'PralineMatchList({}, {})'.format(self.head, self.tail)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.head == other.head and self.tail == other.tail

    def __hash__(self):
        return hash((self.head, self.tail))

class PralineMatchVar(PralineMatchPat):
    def __init__(self, var):
        super().__init__()
        self.var = var

    def match(self, term):
        return {self.var: term}

    def transform(self, transformer):
        return transformer.transform_PralineMatchVar(self)

    def __repr__(self):
        return '{}'.format(self.var)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var == other.var

    def __hash__(self):
        return hash((self.var))

class PralineIf(PralineTerm):
    def __init__(self, cond, e1, e2):
        super().__init__()
        self.cond = cond
        self.e1 = e1
        self.e2 = e2

    def transform(self, transformer):
        return transformer.transform_PralineIf(self)

    def __repr__(self):
        return '(if {} then {} else {})'.format(self.cond, self.e1, self.e2)

    def evaluate(self, prog):
        cond_eval = self.cond.evaluate(prog)
        if cond_eval.is_bool():
            if cond_eval.get_value():
                return self.e1.evaluate(prog)
            else:
                return self.e2.evaluate(prog)
        else:
            raise TypeError('cond should evaluate to a bool in "{}"'.format(self))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.cond == other.cond and self.e1 == other.e1 and self.e2 == other.e2

    def __hash__(self):
        return hash((self.cond, self.e1, self.e2))

class PralinePecanTerm(PralineTerm):
    def __init__(self, pecan_term):
        super().__init__()
        self.pecan_term = pecan_term

    def transform(self, transformer):
        return transformer.transform_PralinePecanTerm(self)

    def __repr__(self):
        return '{{ {} }}'.format(self.pecan_term)

    def evaluate(self, prog):
        return self

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.pecan_term == other.pecan_term

    def __hash__(self):
        return hash((self.pecan_term))

class PralineLambda(PralineTerm):
    def __init__(self, params, body):
        super().__init__()
        self.params = params
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLambda(self)

    def __repr__(self):
        return '(\\ {} -> {})'.format(self.params, self.body)

    def evaluate(self, prog):
        return Closure(prog.praline_env_clone(), self.params, self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.params == other.params and self.body == other.body

    def __hash__(self):
        return hash((self.params, self.body))

class PralineLetPecan(PralineTerm):
    def __init__(self, var, pecan_term, body):
        super().__init__()
        self.var = var
        self.pecan_term = pecan_term
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLetPecan(self)

    def __repr__(self):
        return '(let {} be {} in {})'.format(self.var, self.pecan_term, self.body)

    # TODO
    def evaluate(self, prog):
        raise NotImplementedError

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var == other.var and self.pecan_term == other.pecan_term and self.body == other.body

    def __hash__(self):
        return hash((self.var, self.pecan_term, self.body))

class PralineLet(PralineTerm):
    def __init__(self, var, expr, body):
        self.var = var
        self.expr = expr
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLet(self)

    def __repr__(self):
        return '(let {} := {} in {})'.format(self.var, self.expr, self.body)

    def evaluate(self, prog):
        prog.praline_local_define(self.var.var_name, self.expr)
        result = self.body.evaluate(prog)
        prog.praline_local_cleanup(self.var.var_name)
        return result

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var == other.var and self.expr == other.expr and self.body == other.body

    def __hash__(self):
        return hash((self.var, self.expr, self.body))

class PralineTuple(PralineTerm):
    def __init__(self, vals):
        super().__init__()
        self.vals = vals

    def transform(self, transformer):
        return transformer.transform_PralineTuple(self)

    def __repr__(self):
        return '({})'.format(','.join(map(repr, self.vals)))

    def evaluate(self, prog):
        return PralineTuple([v.evaluate(prog) for v in self.vals])

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.vals == other.vals

    def __hash__(self):
        return hash((self.vals))

    def display(self):
        return '({})'.format(','.join([v.display() for v in self.vals]))

class Closure(PralineTerm):
    def __init__(self, env, args, body):
        super().__init__()
        self.env = env
        self.args = args
        self.body = body

    def evaluate(self, prog):
        return self

    def transform(self, transformer):
        return transformer.transform_Closure(self)

    def __repr__(self):
        return 'Closure({}, {}, {})'.format(self.env, self.args, self.body)

    def apply(self, prog, arg):
        # TODO: This should probably never happen?
        if len(self.args) == 0:
            raise Exception('Clousre accepts no arguments!')

        new_env = dict(self.env)
        new_env[self.args[0].var_name] = arg

        if len(self.args) == 1:
            prog.enter_praline_env(new_env)
            result = self.body.evaluate(prog)
            prog.exit_praline_env()
            return result
        else:
            return Closure(new_env, self.args[1:], self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.env == other.env and self.args == other.args and self.body == other.body

    def __hash__(self):
        return hash((self.args, self.body))

class PralineInt(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineInt(self)

    def __repr__(self):
        return 'PralineInt({})'.format(self.val)

    def evaluate(self, prog):
        return self

    def get_value(self):
        return self.val

    def is_int(self):
        return True

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.args, self.body))

    def display(self):
        return '{}'.format(self.val)

class PralineString(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineString(self)

    def __repr__(self):
        return 'PralineString({})'.format(self.val)

    def evaluate(self, prog):
        return self

    def get_value(self):
        return self.val

    def is_string(self):
        return True

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.args, self.body))

    def display(self):
        return '{}'.format(self.val)

class PralineBool(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineBool(self)

    def __repr__(self):
        return 'PralineBool({})'.format(self.val)

    def evaluate(self, prog):
        return self

    def get_value(self):
        return self.val

    def is_bool(self):
        return True

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.val == other.val

    def __hash__(self):
        return hash((self.args, self.body))

    def display(self):
        return '{}'.format(self.val)

class Builtin(PralineTerm):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def transform(self, transformer):
        return transformer.transform_Builtin(self)

    def __repr__(self):
        return 'BUILTIN({})'.format(self.name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.name == other.name and self.args == other.args

    def __hash__(self):
        return hash(self.name)

    def definition(self):
        return PralineDef(self.name, self.args, self)

class PralineEq(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineEq(self)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

    def evaluate(self, prog):
        return PralineBool(self.a.evaluate(prog) == self.b.evaluate(prog))

class PralineNe(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineNe(self)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        return PralineBool(self.a.evaluate(prog) != self.b.evaluate(prog))

class PralineGe(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineGe(self)

    def __repr__(self):
        return '({} ≥ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineBool(eval_a.get_value() >= eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineLe(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineLe(self)

    def __repr__(self):
        return '({} ≤ {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineBool(eval_a.get_value() <= eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineGt(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineGt(self)

    def __repr__(self):
        return '({} > {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineBool(eval_a.get_value() > eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))

class PralineLt(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineLt(self)

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

    def evaluate(self, prog):
        eval_a = self.a.evaluate(prog)
        eval_b = self.b.evaluate(prog)

        if eval_a.is_int() and eval_b.is_int():
            return PralineBool(eval_a.get_value() < eval_b.get_value())
        else:
            raise TypeError('Both operands should be integers in "{}"'.format(self))
