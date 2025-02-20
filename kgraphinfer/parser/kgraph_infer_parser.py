from lark import Lark, Transformer
import re

# TODO add date, format like "2025-01-01"^Date
# TODO add time, date-time with ^Time and ^DateTime
# TODO add currency with ^Currency(Currency Code), "10.00"^Currency(USD)
# TODO add duration with ^Duration
# TODO add URI/IRI/URN with ^URI
# TODO: add Not
# TODO list comparisons (membership, subset)
# TODO aggregate functions

dsl_grammar = r"""
    start: expression "."
    
    expression: equality | or_group

    or_group: and_group (";" and_group)*
    
    and_group: term ("," term)*
    
    term: not_expr
        | typed_string
        | unification
        | comparison
        | list_comparison
        | aggregation_expr
        | function_call
        | group
        | VAR
        | STRING
        | NUMBER
        | boolean
        | list
        | atom

    not_expr: "not" "(" expression ")"

    group: "(" expression ")"

    unification: VAR "=" (VAR | NUMBER | typed_string | STRING | boolean | list | atom | aggregation_expr)

    equality: value eq_op value
    eq_op: EQUAL

    aggregation_expr: aggregate_operator LBRACE VAR  PIPE  agg_body RBRACE
    agg_body: expression ("," expression)*

    comparison: value COMPARE value

    list_comparison: membership_comparison | subset_comparison

    membership_comparison: value IN list_expr
    subset_comparison: list_expr SUBSET list_expr

    list_expr: VAR | list
    
    function_call: NAME "(" [func_arg ("," func_arg)*] ")"
    func_arg: function_call | VAR | typed_string | STRING | NUMBER | boolean | list

    value: VAR | NUMBER | typed_string | STRING | boolean | list | aggregation_expr

    boolean: TRUE | FALSE

    atom: NAME

    list: "[" [list_items] "]"
    list_items: list_value ("," list_value)*
    list_value: VAR | STRING | NUMBER | typed_string | boolean | list | atom
            
    typed_string: DATE | DATE_TIME | TIME | DURATION | CURRENCY | URI
    
    aggregate_operator: COLLECTION | SET | AVERAGE | SUM | MIN | MAX | COUNT
        
    PIPE: "|"
    COLLECTION: "collection"
    SET: "set"
    AVERAGE: "average"
    SUM: "sum"
    MIN: "min"
    MAX: "max"
    COUNT: "count"

    LBRACE: "{"
    RBRACE: "}"
    EQUAL: "="
    
    TRUE: "true"
    FALSE: "false"
    
    DATE:      /'[^']*'\^Date/
    DATE_TIME: /'[^']*'\^DateTime/
    TIME:      /'[^']*'\^Time/
    DURATION:  /'[^']*'\^Duration/
    CURRENCY:  /'[^']*'\^Currency\([A-Z]+\)/
    URI:       /'[^']*'\^URI/
    
    VAR: "?" /[a-zA-Z0-9_]+/
    
    IN: "in"
    SUBSET: "subset"
    
    AGG_OP: "collection" | "set" | "average" | "sum" | "min" | "max" | "count"

    NUMBER: /-?[0-9]+(\.[0-9]+)?/
    COMPARE: ">" | "<" | ">=" | "<=" | "==" | "!="
    
    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    STRING: "'" /[^']*/ "'"
    
    %import common.WS
    %ignore WS
"""

class KGraphTransformer(Transformer):

    def start(self, items):
        return items[0]

    def expression(self, items):
        # items: either [or_group] or [or_group, EQUAL, or_group]
        if len(items) == 1:
            return items[0]
        else:
            lhs, _, rhs = items
            if isinstance(lhs, str) and lhs.startswith("?"):
                return ("unify", lhs, "=", rhs)
            else:
                return ("equal", lhs, rhs)

    def or_group(self, items):
        return ("OR", items) if len(items) > 1 else items[0]

    def and_group(self, items):
        return ("AND", items) if len(items) > 1 else items[0]

    def group(self, items):
        return ("GROUP", items[0])

    def term(self, items):
        return items[0]

    def not_expr(self, items):
        return ("not", items[0])

    def unification(self, items):
        left, right = items
        return ("unify", left, "=", right)

    def equality(self, items):
        left, _, right = items  # The "=" token is skipped.
        return ("equal", left, right)

    def comparison(self, items):
        left, operator, right = items
        # Because `value` excludes atoms, we only see: VAR, NUMBER, STRING, BOOLEAN, or list
        if isinstance(right, bool) or isinstance(right, list):
            raise ValueError(
                f"Invalid comparison: {left} {operator} {right} (Cannot compare BOOLEAN or LIST values)"
            )
        return ("compare", left, str(operator), right)

    def function_call(self, items):
        name, *args = items
        # (optional) check for nested calls if disallowed
        return ("function", str(name), args)

    def func_arg(self, items):
        return items[0]

    def TRUE(self, _):
        return True

    def FALSE(self, _):
        return False

    def value(self, items):
        return items[0]

    def boolean(self, children):
        return children[0]

    def atom(self, items):
        return ("atom", items[0])

    def list(self, items):
        return items[0] if items else []

    def list_items(self, items):
        return items

    def list_value(self, items):
        return items[0]

    def list_expr(self, items):
        return items[0]

    # List comparison rules
    def membership_comparison(self, items):
        # items: [value, IN, list_expr]
        left = items[0]
        right = items[2]
        return ("in", left, right)

    def subset_comparison(self, items):
        # items: [list_expr, SUBSET, list_expr]
        left = items[0]
        right = items[2]
        return ("subset", left, right)

    def list_comparison(self, items):
        return items[0]

    def aggregation_expr(self, items):
        op_token = items[0]
        op = op_token.value if hasattr(op_token, "value") else str(op_token)
        var = items[2]
        body = items[4]
        return ("aggregate", op, var, body)

    def aggregate_operator(self, items):
        token = items[0]
        return token.value if hasattr(token, "value") else str(token)

    def agg_body(self, items):
        return items

    def VAR(self, token):
        return str(token)

    def STRING(self, token):
        return token[1:-1]  # strip quotes

    def NUMBER(self, token):
        num_str = str(token)
        return float(num_str) if '.' in num_str else int(num_str)

    def NAME(self, token):
        return str(token)

    def DATE(self, token):
        # token.value is like: '2023-02-18'^Date
        val = token.value
        inner = val[1: val.index("'^")]
        return ("date", inner)

    def DATE_TIME(self, token):
        val = token.value
        inner = val[1: val.index("'^")]
        return ("dateTime", inner)

    def TIME(self, token):
        val = token.value
        inner = val[1: val.index("'^")]
        return ("time", inner)

    def DURATION(self, token):
        val = token.value
        inner = val[1: val.index("'^")]
        return ("duration", inner)

    def URI(self, token):
        val = token.value
        inner = val[1: val.index("'^")]
        return ("uri", inner)

    def CURRENCY(self, token):
        val = token.value  # e.g. "'10.00'^Currency(USD)"
        inner = val[1: val.index("'^")]
        m = re.search(r"\^Currency\(([A-Z]+)\)$", val)
        if m:
            code = m.group(1)
            if len(code) != 3:
                raise ValueError(f"Invalid currency code: '{code}'. Expected a 3-letter currency code.")
        else:
            code = None
        return ("currency", inner, code)

    def typed_string(self, items):
        return items[0]

    def COMPARE(self, token):
        return token.value

    def IN(self, token):
        return token

    def SUBSET(self, token):
        return token

    def AGG_OP(self, token):
        return token


class KGraphInferParser:

    def __init__(self):
        self.parser = Lark(dsl_grammar, parser="lalr")
        self.transformer = KGraphTransformer()

    def infer_parse(self, kgraph_infer: str):
        try:
            tree = self.parser.parse(kgraph_infer)
            parsed_result = self.transformer.transform(tree)
            return parsed_result
        except Exception as e:
            # Wrap or re-raise for a friendlier message if desired
            raise e

    def infer_unparse(self, node):
        """
        Convert the parse tree (AST) to a DSL string + final period.
        """
        body = self.ast_to_dsl(node)
        return body + "."

    def ast_to_dsl(self, node):
        """
        Convert the AST node (the structure returned by KGraphTransformer)
        back into a DSL string. This won't reproduce original whitespace or comments,
        but yields a valid DSL expression.
        """
        # 1) If it's a tuple, check its "tag" (the first element) to decide how to handle:
        if isinstance(node, tuple):
            tag = node[0]

            if tag == "AND":
                # node = ('AND', [item1, item2, ...])
                items = node[1]
                return ", ".join(self.ast_to_dsl(i) for i in items)

            elif tag == "OR":
                # node = ('OR', [group1, group2, ...])
                items = node[1]
                return "; ".join(self.ast_to_dsl(i) for i in items)

            elif tag == "not":
                # node = ("not", expr)
                return f"not({self.ast_to_dsl(node[1])})"

            elif tag == "unify":
                # For unification (assignment), left-hand side is a variable.
                return f"{self.ast_to_dsl(node[1])} = {self.ast_to_dsl(node[3])}"
            elif tag == "equal":
                # For equality tests between arbitrary values.
                return f"{self.ast_to_dsl(node[1])} = {self.ast_to_dsl(node[2])}"

            elif tag == "compare":
                # node = ('compare', left, operator_string, right)
                left_side = self.ast_to_dsl(node[1])
                operator = node[2]
                right_side = self.ast_to_dsl(node[3])
                return f"{left_side} {operator} {right_side}"

            elif tag == "function":
                # node = ('function', name_string, [arg1, arg2, ...])
                func_name = node[1]
                args = node[2]
                arg_str = ", ".join(self.ast_to_dsl(a) for a in args)
                return f"{func_name}({arg_str})"

            elif tag == "GROUP":
                # node = ('GROUP', subexpr)
                return f"({self.ast_to_dsl(node[1])})"

            elif tag == "atom":
                # node = ('atom', 'a')
                return node[1]  # just return 'a'

            elif tag == "date":
                return f"'{node[1]}'^Date"
            elif tag == "dateTime":
                return f"'{node[1]}'^DateTime"
            elif tag == "time":
                return f"'{node[1]}'^Time"
            elif tag == "duration":
                return f"'{node[1]}'^Duration"
            elif tag == "uri":
                return f"'{node[1]}'^URI"
            elif tag == "currency":
                return f"'{node[1]}'^Currency({node[2]})"
            elif tag == "in":
                return f"{self.ast_to_dsl(node[1])} in {self.ast_to_dsl(node[2])}"
            elif tag == "subset":
                return f"{self.ast_to_dsl(node[1])} subset {self.ast_to_dsl(node[2])}"
            if tag == "aggregate":
                op = node[1]
                var = node[2]
                body = ", ".join(self.ast_to_dsl(exp) for exp in node[3])
                return f"{op}{{ {var} | {body} }}"
            else:
                # fallback
                return str(node)

        # 2) If it's a list, that likely represents a DSL [ ... ] structure
        elif isinstance(node, list):
            # e.g. [ 'foo', True, 42, ('atom','a') ]
            # Convert each element, separated by ", "
            inner = ", ".join(self.ast_to_dsl(x) for x in node)
            return f"[ {inner} ]"

        # 3) If it's a basic type: str, bool, int/float
        elif isinstance(node, str):
            # We have to decide if it's a variable like "?x" or a raw string that needs quotes.
            # Usually, your AST might keep track of what is a 'STRING' vs a 'VAR' vs an 'atom'.
            # But if you only have a plain Python string here, we must guess.
            # For safety, let's assume:
            # - If it starts with '?' => a var
            # - Otherwise we treat it as a DSL string => re-quote it.
            # But you can adapt to your real structure:
            if node.startswith("?"):
                return node  # it's a variable
            else:
                # We treat it as a DSL string => quote it
                return f"'{node}'"

        elif isinstance(node, bool):
            # DSL booleans are "true"/"false"
            return "true" if node else "false"

        elif isinstance(node, (int, float)):
            return str(node)

        # 4) Fallback
        else:
            return str(node)

    def transform_ast(self, ast, func_call_transform):
        """
        Recursively walk the already-transformed AST, applying 'func_call_transform'
        whenever we see a function call.

        :param ast: The (tuple, list, or basic type) AST returned by query_parse().
        :param func_call_transform: A function that takes a ("function", name, args) node
                                   and returns a (possibly modified) node.

        :return: A new (or mutated) AST node with child nodes transformed.
        """

        # 1) If 'ast' is a tuple, dispatch on the first element to see what node type it is.
        if isinstance(ast, tuple):
            tag = ast[0]

            if tag == "function":
                # ast = ("function", func_name, [arg1, arg2, ...])
                func_name = ast[1]
                args = ast[2]

                # Recursively transform each argument in case they are sub-ASTs.
                new_args = [self.transform_ast(a, func_call_transform) for a in args]
                # Build a new function node with transformed arguments
                new_func_node = ("function", func_name, new_args)

                # Now let the user callback decide how/if to modify this call.
                return func_call_transform(new_func_node)

            elif tag in ("AND", "OR"):
                # e.g. ("AND", [item1, item2, ...]) or ("OR", [item1, item2, ...])
                items = ast[1]
                new_items = [self.transform_ast(i, func_call_transform) for i in items]
                return (tag, new_items)

            elif tag == "unify":
                var_name = ast[1]
                eq = ast[2]
                right_side = ast[3]
                new_right_side = self.transform_ast(right_side, func_call_transform)
                return ("unify", var_name, eq, new_right_side)

            elif tag == "compare":
                left = ast[1]
                op = ast[2]
                right = ast[3]
                new_right = self.transform_ast(right, func_call_transform)
                return ("compare", left, op, new_right)

            elif tag == "GROUP":
                subexpr = ast[1]
                new_subexpr = self.transform_ast(subexpr, func_call_transform)
                return ("GROUP", new_subexpr)

            elif tag == "atom":
                # e.g. ("atom", "a")
                # Typically nothing special to transform, return as-is
                return ast

            elif tag == "not":
                new_expr = self.transform_ast(ast[1], func_call_transform)
                return ("not", new_expr)

            return ast

        elif isinstance(ast, list):
            return [self.transform_ast(item, func_call_transform) for item in ast]

        return ast
