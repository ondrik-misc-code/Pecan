#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.ir import *

def implies(a, b):
    return Disjunction(Complement(a), b)

def iff(a, b):
    return Conjunction(implies(a, b), implies(b, a))

# This class performs a number of simplifications on the IR representation, eliminating constructs that we need to know the type of to eliminate
class TypedIRLowering(IRTransformer):
    def __init__(self, current_program):
        super().__init__()
        self.current_program = current_program

    def transform_Call(self, node):
        # We may need to compute some values for the args
        arg_preds = []
        final_args = []
        for arg in node.args:
            # If it's not just a variable, we need to actually do something
            if type(arg) is not VarRef:
                # For some reason we need to import again here?
                from pecan.lang.ir.arith import Equals, FunctionExpression

                new_var = VarRef(self.current_program.fresh_name()).with_type(arg.get_type())
                arg_preds.append((Equals(arg, new_var), new_var))

                final_args.append(new_var)
            else:
                final_args.append(arg)

        final_pred = Call(node.name, final_args)
        for pred, var in arg_preds:
            final_pred = Exists([var], [None], Conjunction(pred, final_pred))

        return final_pred

    def transform_EqualsCompareRange(self, node):
        idx_var = VarRef(self.current_program.fresh_name()).with_type(node.index_a.start.get_type())

        # We want to make sure that the two words that we are comparing are the same length;
        # Ordinarily, you'd probably use subtraction, but addition is safer because subtraction
        # on natural numbers can be very weird if we go negative
        same_range = Equals(Add(node.index_a.end, node.index_b.start).with_type(node.index_a.end.get_type()),
                            Add(node.index_b.end, node.index_a.start).with_type(node.index_a.end.get_type()))

        # bounds_checks = Conjunction(self.index_a.bounds_check(idx_var), self.index_b.bounds_check(idx_var))
        # Only do bounds check on the first index, because we've verified the bounds are the same
        bounds_checks = node.index_a.bounds_check(idx_var)
        equality_check = self.transform(iff(node.index_a.index_expr(idx_var), node.index_b.index_expr(idx_var)))
        all_equal = Complement(Exists([idx_var], [None], Conjunction(bounds_checks, Complement(equality_check))))
        base_pred = Conjunction(same_range, all_equal)

        if node.is_equals:
            return base_pred
        else:
            return Complement(base_pred)

