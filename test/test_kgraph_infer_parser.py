from kgraphinfer.parser.kgraph_infer_parser import KGraphInferParser

# kgraph_infer = "?x >= ?y, person(?x, father(?y, 'john'))."

parser = KGraphInferParser()

inferences = [
    "?x = ?y, person(?x, 'john', 3), ?age > 18.",
    "a,b,c",
    "'marc'; ('marc', 'marc').",
    "a,b,c.",  # Simple AND
    "a,b;c.",  # Mix of AND & OR
    "(a,b,c),(d,e,f).",  # Grouping with AND
    "(a,b,c);(d,e,f).",  # Grouping with OR
    "person(?x, ?y), friend(?x, ?z); enemy(?y, ?z).",  # Function calls with variables
    "person(?x, father(?y)).",  # INVALID because father(?y) is not a valid function argument
    "?temperature > -5.",
    "?price < 99.99.",
    "?score >= -3.14.",
    "?amount = 100, ?discount = -20.5.",
    "adjustment(?x, -3.5), threshold(5.0).",
    "?is_valid = [ true, false, true ].",  # VALID
    "?is_valid > true.",  # INVALID (Booleans can't be compared)
    "?discount > [10, 20, 30].",  # INVALID (Lists can't be compared)
    "adjustment(?x, -3.5), threshold(5.0).",
    "compute_result(?x, [ happy, 'two', 3, true ]).",
    "test_list(?x, [ true, false ]), person(?y, [ 'Alice', 'Bob' ])."
    ]

for infer in inferences:
    print(f"Infer: {infer}")
    try:
        parsed_infer = parser.infer_parse(infer)
        print("Parsed:", parsed_infer)

        unparsed = parser.infer_unparse(parsed_infer)

        print(f"Unparsed: {unparsed}")

    except Exception as e:
        print("Error:", e)
    print("-" * 50)

# could use to retrieve data, insert into local store,
# and switch function to get from local store instead of remote db

# can use to replace function call with "safe" call or one that include
# module parameter

# can check function names against those that exist by querying ergo

def my_func_rewriter(func_node):
    """
    User-supplied callback that modifies function calls.
    For instance, rename 'get_from_database' to 'get_from_cache'.
    """
    tag, func_name, args = func_node  # should be ("function", <func_name>, <args_list>)
    if func_name == "get_from_database":
        return ("function", "get_from_cache", args)

    if func_name == "bad_infer":
        raise ValueError(
            f"Invalid Function: {func_name}"
        )

    return func_node

# get function/rule names
# clause{?X,?_}, ?X=..?F, ?F[ith(1)->?N]@\btp, ?N=hilog(?FN,?M).
# clause{?X,?_}, ?X=..?F, ?F[ith(1)->?N]@\btp, ?N=hilog(?FN,?M), ?X[term2json->?J]@\json.

# check for a bad / unknown function
ast = parser.infer_parse("?x=5, get_from_database(?id, ?value), bad_infer(?q), ?x > 50.")
print("Original AST:", ast)

try:
    new_ast = parser.transform_ast(ast, my_func_rewriter)
    print("Transformed AST:", new_ast)
except Exception as e:
    print("Error:", e)
