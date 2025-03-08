from itertools import combinations, permutations
from enum import Enum
import isodate
import datetime
from kgraphlang.parser.kgraph_infer_parser import KGraphInferParser

UNBOUND = object()

class EvalResult(Enum):
    YES = "Yes"
    NO = "No"
    UNKNOWN = "Unknown"

    def __str__(self):
        return f"<{self.value}>"
    def __repr__(self):
        return self.__str__()

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

    def __str__(self):
        items = [f"{var}: {value}" for var, value in self.bindings.items()]
        return "{" + ", ".join(items) + "}"

    def __repr__(self):
        return self.__str__()


class AnswerSet:
    """
    Accumulates the final set of answers (each as a dictionary of bindings)
    and stores the overall evaluation result as a structured type.
    """
    def __init__(self):
        self.answers = []
        self.eval_result = EvalResult.UNKNOWN  # Initially unknown

    def add(self, binding: 'BindingStack'):
        self.answers.append(binding.as_dict())

    def get_results(self):
        return self.answers

    def set_eval_result(self, result: EvalResult):
        self.eval_result = result

    def get_eval_result(self):
        return self.eval_result

    def __str__(self):
        return f"Evaluation: {self.eval_result.value}, Answers: {self.answers}"

    def __repr__(self):
        return self.__str__()

# TODO
# atoms (a,b,c) eval?  lookup for existence?
# better exception and error handling
# built in predicates:
# random()

class KGraphInfer:
    """
    Recursively evaluates the AST (nodes like AND, OR, not, GROUP, and predicate calls)
    using a BindingStack for the current variable bindings. The final results are accumulated
    in an AnswerSet.
    """
    def __init__(self, predicate_registry: dict):

        self.parser = KGraphInferParser()
        self.predicate_registry = predicate_registry

    def _compare_generic(self, a, b, operator):

        # checking for type comparisons
        if isinstance(a, bool) and isinstance(b, bool):
            if operator not in ("==", "!="):
                raise ValueError("For booleans, only (in)equality comparisons are allowed")

        if isinstance(a, list) and isinstance(b, list):
            if operator not in ("==", "!="):
                raise ValueError("For lists, only (in)equality comparisons are allowed")

        if isinstance(a, dict) and isinstance(b, dict):
            if operator not in ("==", "!="):
                raise ValueError("For maps, only (in)equality comparisons are allowed")

        # default to generic python handling
        if operator == ">":
            return a > b
        elif operator == "<":
            return a < b
        elif operator == ">=":
            return a >= b
        elif operator == "<=":
            return a <= b
        elif operator == "==":
            return a == b
        elif operator == "!=":
            return a != b
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def _compare_typed(self, left_val, right_val, operator):
        """
        Compare two typed values. Each value is assumed to be a tuple like:
          ("duration", "P3Y6M4DT12H30M5S")
          ("date", "2023-02-18")
          ("dateTime", "2023-02-18T14:00:00")
          ("time", "14:00:00")
          ("currency", "10.00", "USD")
          ("uri", "https://example.com")

        For durations:
          - If either duration includes years or months (nonzero), raise an exception.
          - Otherwise, compare based on total_seconds.
        Other types are handled as before.
        """
        # If either value is not a tuple, fall back to generic comparison.
        if not (isinstance(left_val, tuple) and isinstance(right_val, tuple)):
            return self._compare_generic(left_val, right_val, operator)

        left_type = left_val[0]
        right_type = right_val[0]
        if left_type != right_type:
            raise ValueError(f"Cannot compare different types: {left_type} vs {right_type}")

        if left_type == "uri":
            # Only allow equality comparisons.
            if operator not in ("==", "!="):
                raise ValueError("Only equality comparisons allowed for URIs")
            return (left_val[1] == right_val[1]) if operator == "==" else (left_val[1] != right_val[1])

        elif left_type == "date":
            try:
                left_dt = datetime.datetime.fromisoformat(left_val[1] + "T00:00:00")
                right_dt = datetime.datetime.fromisoformat(right_val[1] + "T00:00:00")
            except Exception as e:
                raise ValueError(f"Error parsing dates: {e}")
            return self._compare_generic(left_dt, right_dt, operator)

        elif left_type == "dateTime":
            try:
                left_dt = datetime.datetime.fromisoformat(left_val[1])
                right_dt = datetime.datetime.fromisoformat(right_val[1])
            except Exception as e:
                raise ValueError(f"Error parsing dateTimes: {e}")
            return self._compare_generic(left_dt, right_dt, operator)

        elif left_type == "time":
            try:
                left_t = datetime.time.fromisoformat(left_val[1])
                right_t = datetime.time.fromisoformat(right_val[1])
            except Exception as e:
                raise ValueError(f"Error parsing times: {e}")
            return self._compare_generic(left_t, right_t, operator)

        elif left_type == "duration":
            try:
                left_d = isodate.parse_duration(left_val[1])
                right_d = isodate.parse_duration(right_val[1])
            except Exception as e:
                raise ValueError(f"Error parsing durations: {e}")
            # Check for presence of years or months.
            left_years = getattr(left_d, "years", 0) or 0
            left_months = getattr(left_d, "months", 0) or 0
            right_years = getattr(right_d, "years", 0) or 0
            right_months = getattr(right_d, "months", 0) or 0
            if (left_years != 0 or left_months != 0 or right_years != 0 or right_months != 0):
                raise ValueError("Cannot compare durations with years or months reliably")
            # Both durations are pure timedeltas.
            return self._compare_generic(left_d.total_seconds(), right_d.total_seconds(), operator)

        elif left_type == "geolocation":
            # Only allow equality or inequality.
            if operator not in ("==", "!="):
                raise ValueError("GeoLocation values can only be compared for equality or inequality.")
            # Compare latitude and longitude for an exact match.
            return (left_val[1] == right_val[1] and left_val[2] == right_val[2]) if operator == "==" else (
                        left_val[1] != right_val[1] or left_val[2] != right_val[2])

        elif left_type == "unit":
            # If the unit URIs differ, then they are not comparable.
            if left_val[2] != right_val[2]:
                  raise ValueError("Cannot compare unit values with different unit types")
            # Attempt to convert the unit values to floats.
            try:
                 left_num = float(left_val[1])
                 right_num = float(right_val[1])
            except Exception:
                  # Fall back to lexicographical comparison if conversion fails.
                  left_num = left_val[1]
                  right_num = right_val[1]
            return self._compare_generic(left_num, right_num, operator)

        elif left_type == "currency":
            if left_val[2] != right_val[2]:
                raise ValueError("Cannot compare currencies of different types")
            try:
                left_amt = float(left_val[1])
                right_amt = float(right_val[1])
            except Exception as e:
                raise ValueError(f"Error parsing currency amounts: {e}")
            return self._compare_generic(left_amt, right_amt, operator)

        # pass-thru cases like list, map
        else:
            return self._compare_generic(left_val[1], right_val[1], operator)

    def _eval_compare(self, node, binding: BindingStack):
        left = node[1]
        operator = node[2]
        right = node[3]
        left_val = self.eval_expr(left, binding)
        right_val = self.eval_expr(right, binding)
        if left_val is UNBOUND or right_val is UNBOUND:
            return []
        try:
            if isinstance(left_val, tuple) and isinstance(right_val, tuple):
                comp = self._compare_typed(left_val, right_val, operator)
            else:
                comp = self._compare_generic(left_val, right_val, operator)
        except Exception as e:
            raise ValueError(f"Error comparing {left_val} and {right_val}: {e}")
        return [binding] if comp else []

    def unify_map_literal(self, binding: BindingStack, pattern_ast, candidate: dict):
        """
        Attempt to unify a left-hand map literal (pattern_ast of the form:
            ('map', [ (pattern_key, pattern_value), ... ])
        ) with a candidate dictionary.
        Tries all permutations of candidate entries.
        Returns a new BindingStack if successful, or None otherwise.
        """
        patterns = pattern_ast[1]  # list of (pattern_key, pattern_value)
        # There must be exactly len(patterns) candidate entries.
        candidate_items = list(candidate.items())
        for perm in permutations(candidate_items):
            new_binding = binding.copy()
            success = True
            for (pat_pair, cand_pair) in zip(patterns, perm):
                pk, pv = pat_pair
                ck, cv = cand_pair
                # Unify key:
                if isinstance(pk, str) and pk.startswith("?"):
                    if pk not in new_binding:
                        new_binding.bind(pk, ck)
                    elif new_binding.get(pk) != ck:
                        success = False
                        break
                else:
                    if pk != ck:
                        success = False
                        break

                if isinstance(pv, str) and pv.startswith("?"):
                    if pv not in new_binding:
                        new_binding.bind(pv, cv)
                    elif new_binding.get(pv) != cv:
                        success = False
                        break
                else:
                    if pv != cv:
                        success = False
                        break
            if success:
                return new_binding
        return None

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

        sub_bindings = self._evaluate_inner(sub_ast, binding.copy())

        results = []

        for b in sub_bindings:
            val = b.get(agg_var)
            if val is not None:
                results.append(val)

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
            elif op == "map":
                d = {}
                for pair in expr[1]:
                    k = self.eval_expr(pair[0], binding)
                    v = self.eval_expr(pair[1], binding)
                    if k is UNBOUND or v is UNBOUND:
                        return UNBOUND
                    d[k] = v
                return d
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
                if len(x) > 0 and x[0] in ("list", "map", "aggregate"):
                    return self.eval_expr(x, binding)
                else:
                    return x
            else:
                return x

        left_val = get_val(left)
        right_val = get_val(right)

        if left_val is UNBOUND and right_val is not UNBOUND:
            binding.bind(left, right_val)
            print(f"Bound {left} to {right_val}")
            return True
        elif right_val is UNBOUND and left_val is not UNBOUND:
            binding.bind(right, left_val)
            return True
        elif left_val is UNBOUND and right_val is UNBOUND:
            return True
        else:
            return left_val == right_val

    def _eval_in(self, node, binding: BindingStack):
        right_val = self.eval_expr(node[2], binding)
        if right_val is UNBOUND:
            return []
        # Case: right is a map.
        if isinstance(right_val, dict):
            # Left operand may be a variable or a map literal.
            if isinstance(node[1], str) and node[1].startswith("?"):
                result_bindings = []
                for key, value in right_val.items():
                    new_binding = binding.copy()
                    new_binding.bind(node[1], {key: value})
                    result_bindings.append(new_binding)
                return result_bindings
            elif isinstance(node[1], tuple) and node[1][0] == "map":
                pattern = node[1]  # raw AST for the map literal
                if len(pattern[1]) != 1:
                    return []
                (pattern_key, pattern_value) = pattern[1][0]
                result_bindings = []
                for candidate_key, candidate_value in right_val.items():
                    new_binding = binding.copy()
                    # Process the key.
                    if isinstance(pattern_key, str) and pattern_key.startswith("?"):
                        if pattern_key not in new_binding:
                            new_binding.bind(pattern_key, candidate_key)
                        elif new_binding.get(pattern_key) != candidate_key:
                            continue
                    else:
                        if pattern_key != candidate_key:
                            continue
                    # Process the value.
                    if isinstance(pattern_value, str) and pattern_value.startswith("?"):
                        if pattern_value not in new_binding:
                            new_binding.bind(pattern_value, candidate_value)
                        elif new_binding.get(pattern_value) != candidate_value:
                            continue
                    else:
                        if pattern_value != candidate_value:
                            continue
                    result_bindings.append(new_binding)
                return result_bindings
            else:
                left_val = self.eval_expr(node[1], binding)
                if left_val is UNBOUND:
                    return []
                return [binding] if left_val in right_val else []
        # Case: right is a list.
        elif isinstance(right_val, list):
            if isinstance(node[1], str) and node[1].startswith("?"):
                result_bindings = []
                for candidate in right_val:
                    new_binding = binding.copy()
                    new_binding.bind(node[1], candidate)
                    result_bindings.append(new_binding)
                return result_bindings
            else:
                left_val = self.eval_expr(node[1], binding)
                if left_val is UNBOUND:
                    return []
                return [binding] if left_val in right_val else []
        else:
            return []

    def _eval_subset(self, node, binding: BindingStack):
        left_val = self.eval_expr(node[1], binding)
        right_val = self.eval_expr(node[2], binding)
        # If both are lists, do a list subset check.
        if isinstance(left_val, list) and isinstance(right_val, list):
            return [binding] if set(left_val).issubset(set(right_val)) else []
        # If right is a map.
        elif isinstance(right_val, dict):
            # Case: left operand is an unbound variable.
            if isinstance(node[1], str) and node[1].startswith("?") and node[1] not in binding:
                items = list(right_val.items())
                result_bindings = []
                n = len(items)
                for i in range(1, 1 << n):  # all non-empty subsets
                    sub = {}
                    for j in range(n):
                        if i & (1 << j):
                            k, v = items[j]
                            sub[k] = v
                    new_binding = binding.copy()
                    new_binding.bind(node[1], sub)
                    result_bindings.append(new_binding)
                return result_bindings
            # Case: left operand is a map literal (pattern).
            elif isinstance(node[1], tuple) and node[1][0] == "map":
                pattern_ast = node[1]
                num_entries = len(pattern_ast[1])
                result_bindings = []
                if len(right_val) < num_entries:
                    return []
                for combo in combinations(list(right_val.items()), num_entries):
                    candidate = dict(combo)
                    new_binding = self.unify_map_literal(binding.copy(), pattern_ast, candidate)
                    if new_binding is not None:
                        result_bindings.append(new_binding)
                return result_bindings
            # Case: left operand is a concrete map.
            elif isinstance(left_val, dict):
                for k, v in left_val.items():
                    if k not in right_val or right_val[k] != v:
                        return []
                return [binding]
            else:
                return []
        else:
            return []

    def _evaluate_inner(self, node, binding: BindingStack):
        if not isinstance(node, tuple):
            return [binding]
        tag = node[0]
        if tag == "AND":
            bindings = [binding]
            for sub in node[1]:
                new_bindings = []
                for b in bindings:
                    new_bindings.extend(self._evaluate_inner(sub, b))
                bindings = new_bindings
            return bindings
        elif tag == "OR":
            results = []
            for sub in node[1]:
                results.extend(self._evaluate_inner(sub, binding.copy()))
            return results
        elif tag == "not":
            sub_bindings = self._evaluate_inner(node[1], binding.copy())
            return [] if sub_bindings else [binding]
        elif tag == "GROUP":
            return self._evaluate_inner(node[1], binding)
        elif tag == "predicate":
            pred_name = node[1]
            args = node[2]
            if pred_name in self.predicate_registry:
                return self.predicate_registry[pred_name].evaluate(args, binding)
            else:
                raise ValueError(f"Unknown predicate: {pred_name}")
        elif tag == "unify":
            new_binding = binding.copy()
            if self.unify_value(new_binding, node[1], node[3]):
                return [new_binding]
            else:
                return []
        elif tag == "math_assign":
            new_binding = binding.copy()
            result = self.eval_arith(node[2], binding)
            if result is UNBOUND:
                return []
            new_binding.bind(node[1], result)
            return [new_binding]
        elif tag == "compare":
            left = node[1]
            operator = node[2]
            right = node[3]
            left_val = self.eval_expr(left, binding)
            right_val = self.eval_expr(right, binding)
            if left_val is UNBOUND or right_val is UNBOUND:
                return []
            try:
                if isinstance(left_val, tuple) and isinstance(right_val, tuple):
                    comp = self._compare_typed(left_val, right_val, operator)
                else:
                    comp = self._compare_generic(left_val, right_val, operator)
            except Exception as e:
                raise ValueError(f"Error comparing {left_val} and {right_val}: {e}")
            return [binding] if comp else []
        elif tag == "in":
            return self._eval_in(node, binding)
        elif tag == "subset":
            return self._eval_subset(node, binding)
        else:
            return [binding]

    def _evaluate(self, node, binding: BindingStack):

        answer_set = AnswerSet()

        results = self._evaluate_inner(node, binding)

        if results and len(results) > 0:
            answer_set.set_eval_result(EvalResult.YES)
        else:
            answer_set.set_eval_result(EvalResult.NO)

        for b in results:
            answer_set.add(b)

        return answer_set

    def execute(self, kg_query: str):

        kgquery_parsed = self.parser.infer_parse(kg_query)

        print(kgquery_parsed)

        initial_binding = BindingStack()

        answer_set = self._evaluate(kgquery_parsed , initial_binding)

        return answer_set

    ################################################################
    # previous eval, refactoring

    def _evaluate_prev(self, node, binding: BindingStack, top_level=False):

        # if top_level:
        #    self.answer_set = AnswerSet()

        if isinstance(node, tuple):
            tag = node[0]
            if tag == "AND":
                bindings = [binding]
                for sub in node[1]:
                    new_bindings = []
                    for b in bindings:
                        new_bindings.extend(self._evaluate(sub, b))
                    bindings = new_bindings
                return bindings
            elif tag == "OR":
                results = []
                for sub in node[1]:
                    results.extend(self._evaluate(sub, binding.copy()))
                return results
            elif tag == "not":
                sub_bindings = self._evaluate(node[1], binding.copy())
                return [] if sub_bindings else [binding]
            elif tag == "GROUP":
                return self._evaluate(node[1], binding)
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
                    print([new_binding])
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
                if right_val is UNBOUND:
                    return []
                left = node[1]

                if isinstance(right_val, dict):
                    result_bindings = []
                    # If the left operand is a map pattern, detect that by checking if
                    # node[1] is a tuple and its first element is "map".
                    if isinstance(node[1], tuple) and node[1][0] == "map":
                        pattern = node[1]  # raw AST for the map literal
                        # For a valid pattern, there should be exactly one key/value pair.
                        if len(pattern[1]) != 1:
                            return []
                        (pattern_key, pattern_value) = pattern[1][0]
                        # For each candidate entry in the right map...
                        for candidate_key, candidate_value in right_val.items():
                            new_binding = binding.copy()
                            # Process the key.
                            if isinstance(pattern_key, str) and pattern_key.startswith("?"):
                                # If unbound, bind it to candidate_key.
                                if pattern_key not in new_binding:
                                    new_binding.bind(pattern_key, candidate_key)
                                elif new_binding.get(pattern_key) != candidate_key:
                                    continue  # candidate doesn't match.
                            else:
                                # Otherwise, the pattern key must match candidate_key exactly.
                                if pattern_key != candidate_key:
                                    continue
                            # Process the value.
                            if isinstance(pattern_value, str) and pattern_value.startswith("?"):
                                if pattern_value not in new_binding:
                                    new_binding.bind(pattern_value, candidate_value)
                                elif new_binding.get(pattern_value) != candidate_value:
                                    continue
                            else:
                                if pattern_value != candidate_value:
                                    continue
                            result_bindings.append(new_binding)
                        return result_bindings
                    # Otherwise, if left operand is a variable, generate one binding per entry.
                    elif isinstance(node[1], str) and node[1].startswith("?"):
                        result_bindings = []
                        for key, value in right_val.items():
                            new_binding = binding.copy()
                            new_binding.bind(node[1], {key: value})
                            result_bindings.append(new_binding)
                        return result_bindings
                    else:
                        # For other cases, evaluate left operand normally and check membership.
                        left_val = self.eval_expr(node[1], binding)
                        if left_val is UNBOUND:
                            return []
                        return [binding] if left_val in right_val else []

                elif isinstance(left, str) and left.startswith("?") and left not in binding:
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

                if isinstance(right_val, dict):
                    # Map–Iteration Case: left operand is an unbound variable.
                    if isinstance(node[1], str) and node[1].startswith("?") and node[1] not in binding:
                        items = list(right_val.items())
                        result_bindings = []
                        n = len(items)
                        # Here, you can generate either the full power set or restrict to subsets of a given size.
                        # For example, if you want all non-empty subsets:
                        for i in range(1, 1 << n):  # skipping the empty set
                            sub = {}
                            for j in range(n):
                                if i & (1 << j):
                                    k, v = items[j]
                                    sub[k] = v
                            new_binding = binding.copy()
                            new_binding.bind(node[1], sub)
                            result_bindings.append(new_binding)
                        return result_bindings
                    # Map–Pattern Case: left operand is a map literal.
                    elif isinstance(node[1], tuple) and node[1][0] == "map":
                        pattern_ast = node[1]  # raw AST for the left-hand map literal
                        num_entries = len(pattern_ast[1])
                        result_bindings = []
                        if len(right_val) < num_entries:
                            return []
                        from itertools import combinations
                        # Generate each combination of right_val entries of size num_entries.
                        for combo in combinations(list(right_val.items()), num_entries):
                            candidate = dict(combo)
                            new_binding = self.unify_map_literal(binding.copy(), pattern_ast, candidate)
                            if new_binding is not None:
                                result_bindings.append(new_binding)
                        return result_bindings
                    # Otherwise, if left_val is a concrete map, do a direct subset check.
                    elif isinstance(left_val, dict):
                        for k, v in left_val.items():
                            if k not in right_val or right_val[k] != v:
                                return []
                        return [binding]
                    else:
                        return []

                if left_val is UNBOUND or right_val is UNBOUND or not isinstance(left_val, list) or not isinstance(
                        right_val, list):
                    return []
                return [binding] if set(left_val).issubset(set(right_val)) else []
            else:
                return [binding]
        else:
            return [binding]

