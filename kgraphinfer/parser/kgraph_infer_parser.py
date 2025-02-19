from lark import Lark, Transformer

# TODO: add Not

dsl_grammar = r"""
    start: expression "."
    expression: or_group

    or_group: and_group (";" and_group)*
    and_group: term ("," term)*

    term: unification
        | comparison
        | function_call
        | group
        | VAR
        | STRING
        | NUMBER
        | BOOLEAN
        | list
        | atom

    group: "(" expression ")"

    unification: VAR "=" (VAR | NUMBER | STRING | BOOLEAN | list | atom)

    comparison: VAR COMPARE value

    function_call: NAME "(" [func_arg ("," func_arg)*] ")"
    func_arg: function_call | VAR | STRING | NUMBER | BOOLEAN | list

    value: VAR | NUMBER | STRING | BOOLEAN | list

    atom: NAME

    list: "[" [list_items] "]"
    list_items: list_value ("," list_value)*
    list_value: STRING | NUMBER | BOOLEAN | list | atom

    BOOLEAN: "true" | "false"
    VAR: "?" /[a-zA-Z0-9_]+/
    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    STRING: "'" /[^']*/ "'"
    NUMBER: /-?[0-9]+(\.[0-9]+)?/
    COMPARE: ">" | "<" | ">=" | "<=" | "==" | "!="
    EQUAL: "="

    %import common.WS
    %ignore WS
"""

class KGraphTransformer(Transformer):
    def start(self, items):
        return items[0]

    def expression(self, items):
        return items[0] if len(items) == 1 else items

    def or_group(self, items):
        return ("OR", items) if len(items) > 1 else items[0]

    def and_group(self, items):
        return ("AND", items) if len(items) > 1 else items[0]

    def group(self, items):
        return ("GROUP", items[0])

    def term(self, items):
        return items[0]

    def unification(self, items):
        left, right = items
        return ("unify", left, "=", right)

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

    def value(self, items):
        return items[0]

    # "atom" method
    def atom(self, items):
        return ("atom", items[0])  # or just `return items[0]`

    def list(self, items):
        return items[0] if items else []

    def list_items(self, items):
        return items

    def list_value(self, items):
        return items[0]

    def BOOLEAN(self, token):
        return True if token == "true" else False

    def VAR(self, token):
        return str(token)

    def STRING(self, token):
        return token[1:-1]  # strip quotes

    def NUMBER(self, token):
        num_str = str(token)
        return float(num_str) if '.' in num_str else int(num_str)

    def NAME(self, token):
        return str(token)

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

            # (1) AND, OR groups
            if tag == "AND":
                # node = ('AND', [item1, item2, ...])
                items = node[1]
                return ", ".join(self.ast_to_dsl(i) for i in items)

            elif tag == "OR":
                # node = ('OR', [group1, group2, ...])
                items = node[1]
                return "; ".join(self.ast_to_dsl(i) for i in items)

            # (2) unification
            elif tag == "unify":
                # node = ('unify', left, '=', right)
                # e.g. ('unify', '?x', '=', ('atom','a'))
                var_name = self.ast_to_dsl(node[1])
                right_side = self.ast_to_dsl(node[3])
                return f"{var_name} = {right_side}"

            # (3) comparison
            elif tag == "compare":
                # node = ('compare', left, operator_string, right)
                left_side = self.ast_to_dsl(node[1])
                operator = node[2]
                right_side = self.ast_to_dsl(node[3])
                return f"{left_side} {operator} {right_side}"

            # (4) function
            elif tag == "function":
                # node = ('function', name_string, [arg1, arg2, ...])
                func_name = node[1]
                args = node[2]
                arg_str = ", ".join(self.ast_to_dsl(a) for a in args)
                return f"{func_name}({arg_str})"

            # (5) group
            elif tag == "GROUP":
                # node = ('GROUP', subexpr)
                return f"({self.ast_to_dsl(node[1])})"

            # (6) atom
            elif tag == "atom":
                # node = ('atom', 'a')
                return node[1]  # just return 'a'

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
                # e.g. ("unify", varName, "=", rightSide)
                var_name = ast[1]
                eq = ast[2]
                right_side = ast[3]
                new_right_side = self.transform_ast(right_side, func_call_transform)
                return ("unify", var_name, eq, new_right_side)

            elif tag == "compare":
                # e.g. ("compare", leftVar, operator, rightVal)
                left = ast[1]
                op = ast[2]
                right = ast[3]
                new_right = self.transform_ast(right, func_call_transform)
                return ("compare", left, op, new_right)

            elif tag == "GROUP":
                # ("GROUP", sub_expr)
                subexpr = ast[1]
                new_subexpr = self.transform_ast(subexpr, func_call_transform)
                return ("GROUP", new_subexpr)

            elif tag == "atom":
                # e.g. ("atom", "a")
                # Typically nothing special to transform, return as-is
                return ast

            # If there's some unrecognized tuple shape, just return it unchanged
            return ast

        # 2) If 'ast' is a list, transform each element
        elif isinstance(ast, list):
            return [self.transform_ast(item, func_call_transform) for item in ast]

        # 3) Otherwise (basic str, int, bool, etc.) return unchanged
        return ast
