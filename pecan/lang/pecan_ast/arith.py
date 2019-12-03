#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.tools.automaton_tools import Substitution, AutomatonTransformer, Projection
from pecan.lang.pecan_ast import *

#TODO: memoize same expressions
#TODO: Problem: can't change automaton for constants if definition of less_than or addition is changed in one run of Pecan.
class Add(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.param = param

    def change_label(self, label): # for changing label to __constant#
        self.label = label

    def show(self):
        return '({} + {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        prog.restrict(self.label, self.a.get_type().get_restriction())
        aut_add = prog.call('adder', [val_a, val_b, self.label])
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_add, result)
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return (result, self.label)

    def transform(self, transformer):
        return transformer.transform_Add(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) + self.b.evaluate_int(prog)

class Sub(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.param = param

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        prog.restrict(self.label, self.a.get_type().get_restriction())
        aut_sub = prog.call('adder', [self.label, val_b, val_a])
        result = spot.product(aut_b, aut_a)
        result = spot.product(aut_sub, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return (result, self.label)

    def transform(self, transformer):
        return transformer.transform_Sub(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) - self.b.evaluate_int(prog)

class Mul(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.param = param
        if not self.a.is_int:
            raise AutomatonArithmeticError("First argument of multiplication must be an integer in {}".format(self))

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)

        c = self.a.evaluate_int(prog)  # copy of a
        if c == 0:
            return IntConst(0).evaluate(prog)

        power = self.b
        sum = IntConst(0)
        while True:
            if c & 1 == 1:
                sum = AutLiteral(Add(power,sum).with_type(self.get_type()).evaluate(prog))
            c = c >> 1
            if c <= 0:
                break
            power = AutLiteral(Add(power, power).with_type(self.get_type()).evaluate(prog))

        return sum.evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Mul(self)

    def show(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) * self.b.evaluate_int(prog)


#TODO:
class Div(BinaryExpression):
    def __init__(self, a, b, param=None):
        super().__init__(a, b)
        self.param = param
        if not self.is_int:
            raise NotImplementedError("Division with automaton hasn't been implemented, sorry. {}".format(self))
        if not self.b.is_int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in {}".format(self))

    def show(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate(self, prog):
        if self.is_int:
            return IntConst(self.evaluate_int(prog)).with_type(self.get_type()).evaluate(prog)
        assert False
        b = self.b.evaluate_int(prog)
        if b == 1:
            return self.a.evaluate(prog)

        (aut_a, val_a) = self.a.evaluate(prog)
        # (aut_b, val_b) = IntConst(b).evaluate(prog)
        #TODO: change label, not finished
        (aut_div,val_div) = Mul(self.b,spot.formula('1').translate()).evaluate(prog)
        def build_div_formula(formula):
            return Substitution({val_div: spot.formula(val_a), 'a': spot.formula('{}_div_{}'.format(val_a,val_a))}).substitute(formula)
        #TODO: drop val_a, val_b in return
        return (spot.product(aut_b, spot.product(aut_a, aut_div)), '{}_add_{}'.format(self.a,self.b))

    def evaluate_int(self, prog):
        assert self.is_int
        if self.a.evaluate_int(prog) % self.b.evaluate_int(prog) != 0:
                raise AutomatonArithmeticError("Division among integers must output an integer in {}".format(self))
        return self.a.evaluate_int(prog) // self.b.evaluate_int(prog)

    def transform(self, transformer):
        return transformer.transform_Div(self)

constants_map = {0: (spot.formula('G(~__constant0)').translate(), "__constant0")}
class IntConst(Expression):
    # Constant 0 is defined as 000000...
    def __init__(self, val, param=None):
        super().__init__()
        self.val = val
        self.label = "__constant{}".format(self.val)
        self.param = param

    def evaluate(self,prog):
        # TODO: Put constants map back, after we figure out how to do it for the various changing bases/numeration
        #  systems
        zero_const_var  = VarRef("__constant0").with_type(self.get_type())
        zero_const = IntConst(0).with_type(self.get_type())
        one_const_var = VarRef("__constant1").with_type(self.get_type())
        b_const = VarRef('b').with_type(self.get_type())

        # if self.val in constants_map:
        #     return constants_map[self.val]
        if self.val == 0:
            # TODO: For some reason, the below definition doesn't work
            # formula_0 = Forall('b', LessEquals(zero_const_var, b_const))
            # return formula_0.evaluate(prog), zero_const_var.var_name

            return constants_map[0]
        if self.val == 1:
            formula_1 = Conjunction(Less(zero_const, one_const_var), Forall('b', Implies(Less(zero_const, b_const), LessEquals(one_const_var, b_const))))
            constants_map[1] = (formula_1.evaluate(prog), one_const_var.var_name)
            return constants_map[1]

        assert self.val >= 2, "constant here should be greater than or equal to 1, while it is {}".format(self.val)

        if self.val & (self.val - 1) == 0:
            half = IntConst(self.val // 2).with_type(self.get_type())
            result = Add(half, half)
        else:
            c = self.val
            power = 1
            while c != 1:
                power  = power << 1
                c = c >> 1
            result = Add(IntConst(power).with_type(self.get_type()), IntConst(self.val - power).with_type(self.get_type()))

        result.change_label(self.label)
        result.is_int = False
        (result,val) = result.evaluate(prog)
        constants_map[self.val] = (result,val)
        return constants_map[self.val]

    def evaluate_int(self, prog):
        return self.val

    def transform(self, transformer):
        return transformer.transform_IntConst(self)

    def show(self):
        return str(self.val)

class Equals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) == self.b.evaluate_int(prog) else spot.formula('0').translate()

        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        eq_aut = spot.formula('G(({0} -> {1}) & ({1} -> {0}))'.format(val_a, val_b)).translate()
        result = spot.product(eq_aut, spot.product(aut_a, aut_b))
        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return result

    def transform(self, transformer):
        return transformer.transform_Equals(self)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) != self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Complement(Equals(self.a, self.b)).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_NotEquals(self)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

class Less(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) < self.b.evaluate_int(prog) else spot.formula('0').translate()
        (aut_a, val_a) = self.a.evaluate(prog)
        (aut_b, val_b) = self.b.evaluate(prog)
        aut_less = prog.call(prog.context['less'], [val_a, val_b])
        result = spot.product(aut_a, aut_b)
        result = spot.product(aut_less, result)

        proj_vars = set()
        if type(self.a) is not VarRef:
            proj_vars.add(val_a)
        if type(self.b) is not VarRef:
            proj_vars.add(val_b)
        result = Projection(result, proj_vars).project()
        return result

    def transform(self, transformer):
        return transformer.transform_Less(self)

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

class Greater(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Less(self.b,self.a).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Greater(self)

    def __repr__(self):
        return '({} > {})'.format(self.a, self.b)

class LessEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) <= self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Disjunction(Less(self.a,self.b),Equals(self.a,self.b)).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_LessEquals(self)

    def __repr__(self):
        return '({} ≤ {})'.format(self.a, self.b)

class GreaterEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) >= self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Disjunction(Less(self.b,self.a),Equals(self.a,self.b)).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_GreaterEquals(self)

    def __repr__(self):
        return '({} ≥ {})'.format(self.a, self.b)

class Neg(UnaryExpression): # Should this be allowed?
    def __init__(self, a):
        super().__init__(a)
        self.a = a

    def transform(self, transformer):
        return transformer.transform_Neg(self)

    def show(self):
        return '(-{})'.format(self.a)

    def evaluate(self, prog):
        if self.a.is_int:
            return IntConst(self.evaluate_int(prog)).evaluate(prog)
        raise AutomatonArithmeticError("Should not negate automaton in {}".format(self))
        # return Sub(IntConst(0),self.a).evaluate(prog)

    def evaluate_int(self, prog):
        assert self.is_int
        return -self.a.evaluate_int(prog)

class AutomatonArithmeticError(Exception):
    pass
