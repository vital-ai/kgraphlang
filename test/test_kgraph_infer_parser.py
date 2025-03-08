from kgraphlang.parser.kgraph_infer_parser import KGraphInferParser, KGraphTransformer
from lark import Tree, Token

def main():

    parser = KGraphInferParser()

    inferences = [
        "?x = ?y, person(?x, 'john', 3), ?age > 18.",
        "a,b,c",
        "'marc'; ('marc', 'marc').",
        "a,b,c.",  # Simple AND
        "a,b;c.",  # Mix of AND & OR
        "(a,b,c),(d,e,f).",  # Grouping with AND
        "(a,b,c);(d,e,f).",  # Grouping with OR
        "person(?x, ?y), friend(?x, ?z); enemy(?y, ?z).",  # predicate calls with variables
        "person(?x, father(?y)).",  # INVALID because father(?y) is not a valid predicate argument
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

        "?X = '40.7128,-74.0060'^GeoLocation.",

        "?X = '100.0'^Unit('http://qudt.org/vocab/unit/kg').",

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

        '?X = "hello".',

        # multi-line string mainly would come up in unification cases,
        # but it should work in the same places as double/single quoted string

        '''?X = """hello
there
how
are
you?
""", ?Y = "Great!".    
        ''',

        # a Map is a collection of entries of k=v, with unique k
        # a Map can be compared with another Map via "subset"
        # which aligns a subset of entries from one to the other
        # in contrast, a single-entry Map can be compared to a Map via "in"
        # which aligns the single entry to the target Map

        # an unbound set of 3 k=v subset a 10 entry map would find 120 combinations (10 choose 3)
        # an unbound k=v in 10 a entry Map would find 10 entries

        """
        ?uri_prop = 'urn:uri_prop'^URI,
        ?name_prop = 'urn:name_prop'^URI,
        ?email_prop = 'urn:email_prop'^URI,
    
        person_uri_list(?PersonList), 
        
        ?PersonEmailMapList = collection { 
            
            ?PersonMapRecord | 
            
            ?Pid in ?PersonList, 
            get_person_map(?Pid, ?PersonMap),
             
            [ 
                ?uri_prop = ?Pid,
                ?name_prop = ?Name,
                ?email_prop = ?Email
            ] subset ?PersonMap,
            
            ?PersonMapRecord = [
                ?uri_prop = ?Pid,
                ?name_prop = ?Name,
                ?email_prop = ?Email
            ] 
        }.""",

        """
            ?uri_prop = 'urn:uri_prop'^URI,
            ?name_prop = 'urn:name_prop'^URI,
            ?email_prop = 'urn:email_prop'^URI,
        
            person_uri_list(?PersonList), 
        
            ?PersonEmailMapList = collection { 
        
                ?PersonMapRecord | 
        
                ?Pid in ?PersonList,
                
                ?prop_list = [ ?uri_prop, ?name_prop, ?email_prop ],
                 
                get_person_map(?Pid, ?prop_list, ?PersonMapRecord)
        
            }.""",


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
    # and switch predicate to get from local store instead of remote db

    # can use to replace predicate call with "safe" call or one that include
    # module parameter

    # could use to do a separate request like get_summary(file_path, ?summary)
    # and replace with a lookup of that summary that's been generated

    # can check predicate names against those that exist by querying ergo

    def my_predicate_rewriter(predicate_node):
        """
        User-supplied callback that modifies predicate calls.
        For instance, rename 'get_from_database' to 'get_from_cache'.
        """
        tag, predicate_name, args = predicate_node  # should be ("predicate", <predicate_name>, <args_list>)
        if predicate_name == "get_from_database":
            return ("predicate", "get_from_cache", args)

        # this could check names against a known list and return
        # an error if a predicate is not found
        # in this case we're just checking for a known predicate to test throwing an error
        if predicate_name == "bad_infer":
            raise ValueError(
                f"Invalid Predicate: {predicate_name}"
            )

        return predicate_node

    # get predicate/rule names
    # clause{?X,?_}, ?X=..?F, ?F[ith(1)->?N]@\btp, ?N=hilog(?FN,?M).
    # clause{?X,?_}, ?X=..?F, ?F[ith(1)->?N]@\btp, ?N=hilog(?FN,?M), ?X[term2json->?J]@\json.

    # test transform

    ast = parser.infer_parse("?x=5, get_from_database(?id, ?value), ?x > 50.")
    print("Original AST:", ast)

    try:
        new_ast = parser.transform_ast(ast, my_predicate_rewriter)
        print("Transformed AST:", new_ast)
    except Exception as e:
        print("Error:", e)


    # check for a bad / unknown predicate
    ast = parser.infer_parse("?x=5, get_from_database(?id, ?value), bad_infer(?q), ?x > 50.")
    print("Original AST:", ast)

    try:
        new_ast = parser.transform_ast(ast, my_predicate_rewriter)
        print("Transformed AST:", new_ast)
    except Exception as e:
        print("Error:", e)


    # Manually creating a parse tree and then "unparse" it
    # could be used for a case of generating a string to pass to the LLM, such as for inference/query results
    # that were generated elsewhere or transformed from the kgraph results
    # this could include when the underlying kgraph does not have a convenient map representation
    # and we want to put data in that format

    item1 = Tree('map_item', [
        Tree('map_key', [Token('VAR', '?uri_prop')]),
        Tree('map_value', [Token('VAR', '?Pid')])
    ])

    item2 = Tree('map_item', [
        Tree('map_key', [Token('VAR', '?name_prop')]),
        Tree('map_value', [Token('VAR', '?Name')])
    ])

    item3 = Tree('map_item', [
        Tree('map_key', [Token('VAR', '?email_prop')]),
        Tree('map_value', [Token('VAR', '?Email')])
    ])

    map_collection = Tree('map_collection', [item1, item2, item3])

    bracketed_collection = Tree('bracketed_collection', [map_collection])

    unification_tree = Tree('unification', [
        # Left-hand side: a VAR node.
        Tree('VAR', [Token('VAR', '?m')]),
        # The literal "=" token; your transformer ignores it.
        Token('EQUAL', '='),
        # Right-hand side: our previously constructed bracketed collection.
        bracketed_collection
    ])


    print(bracketed_collection.pretty())

    infer_parser = KGraphInferParser()

    ast = infer_parser.transformer.transform(bracketed_collection)
    print("Transformed AST:")
    print(ast)

    dsl_str = infer_parser.infer_unparse(ast)
    print("Unparsed DSL:")
    print(dsl_str)

    # everything is a string
    item1 = Tree('map_item', [
        Tree('map_key', [Token('STRING', "'foo'")]),
        Tree('map_value', [Token('STRING', "'bar'")])
    ])
    item2 = Tree('map_item', [
        Tree('map_key', [Token('STRING', "'key1'")]),
        Tree('map_value', [Token('STRING', "'value1'")])
    ])
    item3 = Tree('map_item', [
        Tree('map_key', [Token('STRING', "'key2'")]),
        Tree('map_value', [Token('STRING', "'value2'")])
    ])

    map_collection = Tree('map_collection', [item1, item2, item3])

    bracketed_collection = Tree('bracketed_collection', [map_collection])

    print(bracketed_collection.pretty())

    infer_parser = KGraphInferParser()

    ast = infer_parser.transformer.transform(bracketed_collection)
    print("Transformed AST:")
    print(ast)

    dsl_str = infer_parser.infer_unparse(ast)
    print("Unparsed DSL:")
    print(dsl_str)


    # some types don't need token wrapper
    item1 = Tree('map_item', [
        Tree('map_key', ['foo']),
        Tree('map_value', [32])
    ])
    item2 = Tree('map_item', [
        Tree('map_key', ['key1']),
        Tree('map_value', ['value1'])
    ])
    item3 = Tree('map_item', [
        Tree('map_key', ['key2']),
        Tree('map_value', ['value2'])
    ])

    map_collection = Tree('map_collection', [item1, item2, item3])

    bracketed_collection = Tree('bracketed_collection', [map_collection])

    infer_parser = KGraphInferParser()

    ast = infer_parser.transformer.transform(bracketed_collection)
    print("Transformed AST:")
    print(ast)

    dsl_str = infer_parser.infer_unparse(ast)
    print("Unparsed DSL:")
    print(dsl_str)


    # some cases do need the wrapper such as typed strings
    item1 = Tree('map_item', [
        Tree('map_key', [Token('URI', "'http://example.com/resource1'^URI")]),
        Tree('map_value', [Token('DATE', "'2023-02-18'^Date")])
    ])

    # Item 2: key is a URI, value is a TIME.
    item2 = Tree('map_item', [
        Tree('map_key', [Token('URI', "'http://example.com/resource2'^URI")]),
        Tree('map_value', [Token('TIME', "'12:34:56'^Time")])
    ])

    # Item 3: key is a URI, value is a CURRENCY.
    item3 = Tree('map_item', [
        Tree('map_key', [Token('URI', "'http://example.com/resource3'^URI")]),
        Tree('map_value', [Token('CURRENCY', "'10.00'^Currency(USD)")])
    ])

    # Group the map items into a map_collection.
    map_collection = Tree('map_collection', [item1, item2, item3])

    # Wrap the collection in a bracketed_collection node.
    bracketed_collection = Tree('bracketed_collection', [map_collection])

    infer_parser = KGraphInferParser()

    ast = infer_parser.transformer.transform(bracketed_collection)
    print("Transformed AST:")
    print(ast)

    dsl_str = infer_parser.infer_unparse(ast)
    print("Unparsed DSL:")
    print(dsl_str)


if __name__ == "__main__":
    main()


