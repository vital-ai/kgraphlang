
UNBOUND = object()

class BindingStack:
    """
    Represents the current set of variable bindings.
    """
    def __init__(self, bindings=None):
        self.bindings = bindings.copy() if bindings else {}

    def copy(self):
        return BindingStack(self.bindings)

    def bind(self, var, value):
        """
        Bind variable 'var' to 'value'. If already bound, the value must match.
        Returns True if the binding is valid.
        """
        if var in self.bindings:
            return self.bindings[var] == value
        self.bindings[var] = value
        return True

    def bind_copy(self, var, value):
        """
        Returns a new BindingStack with var bound to value.
        """
        new_binding = self.copy()
        new_binding.bind(var, value)
        return new_binding

    def get(self, var):
        return self.bindings.get(var)

    def __contains__(self, var):
        return var in self.bindings

    def as_dict(self):
        return self.bindings.copy()


# TODO add a bool yes/no for eval-ing
class AnswerSet:
    """
    Accumulates the final set of answers (each as a dictionary of bindings).
    """
    def __init__(self):
        self.answers = []

    def add(self, binding: BindingStack):
        self.answers.append(binding.as_dict())

    def get_results(self):
        return self.answers

# TODO
# eval-ing true without binds
# math expressions and is
# lists and subset / in
# aggregation functions
# comparisons including types strings
# atoms (a,b,c) eval?  lookup for existence?
# map cases

# TODO
# better exception and error handling

# TODO
# built in predicates:
# random()

class KGraphInfer:
    """
    Recursively evaluates the AST (nodes like AND, OR, not, GROUP, and predicate calls)
    using a BindingStack for the current variable bindings. The final results are accumulated
    in an AnswerSet.
    """
    def __init__(self, predicate_registry: dict):
        self.predicate_registry = predicate_registry
        self.answer_set = AnswerSet()

    def get_value(self, x, binding: BindingStack):

        if isinstance(x, str) and x.startswith("?"):
            val = binding.get(x) if x in binding else UNBOUND
            # If the value is a tuple representing a list, evaluate it.
            if isinstance(val, tuple) and len(val) > 0 and val[0] == "list":
                return self.eval_expr(val, binding)
            return val
        elif isinstance(x, tuple) and len(x) > 0 and x[0] == "list":
            return self.eval_expr(x, binding)
        else:
            return x

    def evaluate_aggregate(self, agg_node, binding: BindingStack):
        """
        Evaluate an aggregate node of the form:
           ('aggregate', op, agg_var, body)
        where body is a list of expressions (the aggregate query).
        Returns the aggregated value.
        """
        op = agg_node[1]
        agg_var = agg_node[2]
        body = agg_node[3]  # a list of one or more expressions
        if len(body) == 1:
            sub_ast = body[0]
        else:
            sub_ast = ("AND", body)
        sub_bindings = self.evaluate(sub_ast, binding.copy())
        results = []
        for b in sub_bindings:
            val = b.get(agg_var)
            if val is not None:
                results.append(val)

        # print(results)

        if op == "collection":
            return results
        elif op == "set":
            # Convert each result to a tuple if it is a list, otherwise use it directly.
            hashed = [tuple(r) if isinstance(r, list) else r for r in results]
            return list(set(hashed))
        elif op == "count":
            return len(results)
        elif op == "sum":
            try:
                return sum(results)
            except Exception:
                return UNBOUND
        elif op == "average":
            try:
                return sum(results) / len(results) if results else UNBOUND
            except Exception:
                return UNBOUND
        elif op == "min":
            try:
                return min(results)
            except Exception:
                return UNBOUND
        elif op == "max":
            try:
                return max(results)
            except Exception:
                return UNBOUND
        else:
            return UNBOUND

    def eval_expr(self, expr, binding: BindingStack):
        """
        Recursively evaluate an expression to a concrete value.
        If the expression is a tuple and its first element is an arithmetic operator,
        use eval_arith; otherwise, if we cannot resolve it to a literal value,
        return UNBOUND.
        """

        # print(expr)

        if isinstance(expr, tuple):
            op = expr[0]
            if op in ("add", "sub", "mul", "div"):
                return self.eval_arith(expr, binding)
            elif op == "list":
                result = []
                for item in expr[1]:
                    v = self.eval_expr(item, binding)
                    if v is UNBOUND:
                        return UNBOUND
                    result.append(v)
                return result
            elif op == "aggregate":
                return self.evaluate_aggregate(expr, binding)
            else:
                return UNBOUND
        elif isinstance(expr, str) and expr.startswith("?"):
            return binding.get(expr) if expr in binding else UNBOUND
        else:
            # Literal value (number, string, etc.)
            return expr

    def eval_arith(self, expr, binding: BindingStack):
        """
        Recursively evaluates an arithmetic expression represented as a tuple.
        The expression can be:
          - A tuple like ('add', left, right)
          - A number (int/float)
          - A variable (e.g. '?y') that must already be bound.
        Returns the computed value or UNBOUND if a variable is not bound.
        """
        if isinstance(expr, tuple):
            op = expr[0]
            if op == "add":
                left = self.eval_arith(expr[1], binding)
                right = self.eval_arith(expr[2], binding)
                if left is UNBOUND or right is UNBOUND:
                    return UNBOUND
                return left + right
            elif op == "sub":
                left = self.eval_arith(expr[1], binding)
                right = self.eval_arith(expr[2], binding)
                if left is UNBOUND or right is UNBOUND:
                    return UNBOUND
                return left - right
            elif op == "mul":
                left = self.eval_arith(expr[1], binding)
                right = self.eval_arith(expr[2], binding)
                if left is UNBOUND or right is UNBOUND:
                    return UNBOUND
                return left * right
            elif op == "div":
                left = self.eval_arith(expr[1], binding)
                right = self.eval_arith(expr[2], binding)
                if left is UNBOUND or right is UNBOUND or right == 0:
                    return UNBOUND
                return left / right
            else:
                # Fallback: try evaluating the second element (for grouped expressions)
                return self.eval_arith(expr[1], binding)
        else:
            # If it's a variable, return its binding (or UNBOUND if not bound)
            if isinstance(expr, str) and expr.startswith("?"):
                return binding.get(expr) if expr in binding else UNBOUND
            else:
                # Assume it's a number literal or other literal value.
                return expr

    def unify_value(self, binding: BindingStack, left, right):
        def get_val(x):
            if isinstance(x, str) and x.startswith("?"):
                return binding.get(x) if x in binding else UNBOUND
            # If x is a tuple tagged as "list", evaluate it to get a concrete list.
            elif isinstance(x, tuple):
                if len(x) > 0 and x[0] in ("list", "aggregate"):
                    return self.eval_expr(x, binding)
                else:
                    return x
            else:
                return x

        left_val = get_val(left)
        right_val = get_val(right)
        if left_val is UNBOUND and right_val is not UNBOUND:
            binding.bind(left, right_val)
            return True
        elif right_val is UNBOUND and left_val is not UNBOUND:
            binding.bind(right, left_val)
            return True
        elif left_val is UNBOUND and right_val is UNBOUND:
            return True
        else:
            return left_val == right_val

    def evaluate(self, node, binding: BindingStack):
        if isinstance(node, tuple):
            tag = node[0]
            if tag == "AND":
                bindings = [binding]
                for sub in node[1]:
                    new_bindings = []
                    for b in bindings:
                        new_bindings.extend(self.evaluate(sub, b))
                    bindings = new_bindings
                return bindings
            elif tag == "OR":
                results = []
                for sub in node[1]:
                    results.extend(self.evaluate(sub, binding.copy()))
                return results
            elif tag == "not":
                sub_bindings = self.evaluate(node[1], binding.copy())
                return [] if sub_bindings else [binding]
            elif tag == "GROUP":
                return self.evaluate(node[1], binding)
            elif tag == "predicate":
                pred_name = node[1]
                args = node[2]
                if pred_name in self.predicate_registry:
                    return self.predicate_registry[pred_name].evaluate(args, binding)
                else:
                    raise ValueError(f"Unknown predicate: {pred_name}")
            elif tag == "unify":
                # Node structure: ("unify", left, "=", right)
                new_binding = binding.copy()
                if self.unify_value(new_binding, node[1], node[3]):
                    return [new_binding]
                else:
                    return []
            elif tag == "math_assign":
                # Node structure: ("math_assign", var, arith_expr)
                new_binding = binding.copy()
                result = self.eval_arith(node[2], binding)
                if result is UNBOUND:
                    return []
                new_binding.bind(node[1], result)
                return [new_binding]
            elif tag == "compare":
                # Node structure: ("compare", left, operator, right)
                left = node[1]
                operator = node[2]
                right = node[3]
                # left_val = self.get_value(left, binding)
                # right_val = self.get_value(right, binding)

                left_val = self.eval_expr(left, binding)
                right_val = self.eval_expr(right, binding)

                if left_val is UNBOUND or right_val is UNBOUND:
                    return []
                result = False
                if operator == ">":
                    result = left_val > right_val
                elif operator == "<":
                    result = left_val < right_val
                elif operator == ">=":
                    result = left_val >= right_val
                elif operator == "<=":
                    result = left_val <= right_val
                elif operator == "==":
                    result = left_val == right_val
                elif operator == "!=":
                    result = left_val != right_val
                return [binding] if result else []
            elif tag == "in":
                right_val = self.eval_expr(node[2], binding)
                if right_val is UNBOUND or not isinstance(right_val, list):
                    return []
                left = node[1]
                # If left is an unbound variable, generate a binding for each candidate.
                if isinstance(left, str) and left.startswith("?") and left not in binding:
                    result_bindings = []
                    for candidate in right_val:
                        new_binding = binding.copy()
                        new_binding.bind(left, candidate)
                        result_bindings.append(new_binding)
                    return result_bindings
                else:
                    left_val = self.eval_expr(left, binding)
                    if left_val is UNBOUND:
                        return []
                    return [binding] if left_val in right_val else []
            elif tag == "subset":
                left = node[1]
                right = node[2]

                left_val = self.eval_expr(left, binding)
                right_val = self.eval_expr(right, binding)

                # print(f"{{{left_val}}} subset of {{{right_val}}}")


                if left_val is UNBOUND or right_val is UNBOUND or not isinstance(left_val, list) or not isinstance(
                        right_val, list):
                    return []
                return [binding] if set(left_val).issubset(set(right_val)) else []
            else:
                return [binding]
        else:
            return [binding]

    def run(self, ast):
        initial_binding = BindingStack()
        results = self.evaluate(ast, initial_binding)
        for b in results:
            self.answer_set.add(b)
        return self.answer_set.get_results()

