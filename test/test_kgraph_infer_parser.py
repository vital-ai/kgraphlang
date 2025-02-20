from kgraphinfer.parser.kgraph_infer_parser import KGraphInferParser

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
    "test_list(?x, [ true, false ]), person(?y, [ 'Alice', 'Bob' ]).",

    "not(?x = 'value').",

    "not(person(?x, 'john')).",

    "person(?X), not( ( enemy(?X); frenemy(?X) ) ), get_email(?X, ?M).",

    "?event_date = '2023-02-18'^Date.",

    "'2023-02-18'^Date >= '2023-02-18'^Date.",

    "'2023-02-18'^Date >= ?event_date.",

    "?event_datetime = '2023-02-18T14:00:00'^DateTime.",
    "?meeting_time = '14:30'^Time.",
    "?duration = 'P3Y6M4DT12H30M5S'^Duration.",
    "?price = '10.00'^Currency(USD).",
    "?price = '10.00'^Currency(B).",
    "?price = '10.00'^Currency(ALPHA).",
    "?website = 'https://example.com'^URI.",

    "?x in ['a', 'b', 'c'].",
    "['a','b'] subset ['a','b','c'].",
    "?x subset ?y.",
    "?x = 42, ?x > 10.",
    "[?x,'b'] subset ['a',?y,'c'].",

    "?friend_list = collection { ?friend_tuple | person(?p), not(enemy_of(?p, ?friend)), friend_of(?p, ?friend), ?friend_tuple = [?p, ?friend] }.",

    "5 = count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    "5 >= count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    "?x < count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    "?x = count{ ?item | tasty(?item), ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    "?total = sum{ ?value | get_property(?x, 'hasScore', ?value) }.",

    "?avg = average{ ?score | get_property(?x, 'hasScore', ?score) }.",

    "?x is ?y + 5.",

    "?x > ( ?y / 10.0 ) * 5.0.",

    "?x is ?y + 5, ?x < count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    "?x is ?y + 5; ?x < count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    # note: this is a little ambiguous about the treatment of: ( a;b;c,(d,f))
    "?x is ?y + 5; ?y > 5 + 5, ( a;b;c,(d,f) ), ?x < count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    # note: this removes the ambiguity by putting parenthesis around (a;b;c)
    "?x is ?y + 5; ?y > 5 + 5, ( (a;b;c),(d,f)), ?x < count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    # Note: AND binds more tightly which makes it a;b; + c,(d,f)
    "a;b;c,(d,f).",

    "(a;b;c),(d,f).",

    "outer(inner(?x)).",
    # this should not parse because aggregation can't directly be included in a math function
    "?x is ?y + count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }.",

    # this moves the aggregation result into a variable and then uses the variable in math
    "?count = count{ ?item | ?item in ['apple', 'orange', 'banana', 'grape', 'pear'] }, ?x is ?y + ?count.",

    "['123' = ?value] in ?map.",

    "?m = [ 'foo' = 'bar', ?k = 42 ].",

    "[ 'foo' = 'bar' ] subset [ 'foo' = 'bar', 'answer' = 42 ].",

    "?nested_map = [ 'outer' = [ 'inner_key' = [ 1, 2, 3 ] ] ].",

    "?sum = sum{ ?v | [ ?k = ?v ] in ?map }.",

    "?sum = sum{ ?v | [ 'k' = ?v ] in [ 'k' = 10, 'other' = true, 'k' = 20 ] }.",

    "?sum = sum{ ?v | [ ?k = ?v ] in [ 'k1' = 10, 'k2' = 15, 'k3' = 20 ] }.",

    "?k = 'answer', ?m = [ 'urn:uri_prop'^URI = 'urn:123'^URI, ?k = 42 ].",

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

# could use to do a separate request like get_summary(file_path, ?summary)
# and replace with a lookup of that summary that's been generated

# can check function names against those that exist by querying ergo

def my_func_rewriter(func_node):
    """
    User-supplied callback that modifies function calls.
    For instance, rename 'get_from_database' to 'get_from_cache'.
    """
    tag, func_name, args = func_node  # should be ("function", <func_name>, <args_list>)
    if func_name == "get_from_database":
        return ("function", "get_from_cache", args)

    # this could check names against a known list and return
    # an error if a function is not found
    # in this case we're just checking for a known function to test throwing an error
    if func_name == "bad_infer":
        raise ValueError(
            f"Invalid Function: {func_name}"
        )

    return func_node

# get function/rule names
# clause{?X,?_}, ?X=..?F, ?F[ith(1)->?N]@\btp, ?N=hilog(?FN,?M).
# clause{?X,?_}, ?X=..?F, ?F[ith(1)->?N]@\btp, ?N=hilog(?FN,?M), ?X[term2json->?J]@\json.

# test transform

ast = parser.infer_parse("?x=5, get_from_database(?id, ?value), ?x > 50.")
print("Original AST:", ast)

try:
    new_ast = parser.transform_ast(ast, my_func_rewriter)
    print("Transformed AST:", new_ast)
except Exception as e:
    print("Error:", e)


# check for a bad / unknown function
ast = parser.infer_parse("?x=5, get_from_database(?id, ?value), bad_infer(?q), ?x > 50.")
print("Original AST:", ast)

try:
    new_ast = parser.transform_ast(ast, my_func_rewriter)
    print("Transformed AST:", new_ast)
except Exception as e:
    print("Error:", e)
