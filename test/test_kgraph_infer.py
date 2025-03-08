from kgraphlang.filter_infer.filter_predicate import FilterPredicate
from kgraphlang.kgraph_infer import KGraphInfer

class PersonPredicate(FilterPredicate):
    def get_candidates(self):
        # Each candidate is a 1-tuple representing a person.
        return [("Alice",), ("Bob",), ("Charlie",)]

class EnemyPredicate(FilterPredicate):
    def get_candidates(self):
        # Each candidate is a 1-tuple representing an enemy.
        return [("Bob",)]

class FrenemyPredicate(FilterPredicate):
    def get_candidates(self):
        # Each candidate is a 1-tuple representing a frenemy.
        return [("Charlie",)]

class GetEmailPredicate(FilterPredicate):
    def get_candidates(self):
        # Each candidate is a 2-tuple: (person, email)
        return [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
            ("Charlie", "charlie@example.com")
        ]

class GetPropertyPredicate(FilterPredicate):
    """
    A predicate that retrieves a property value. For example, given a person and a property
    name (e.g. 'age'), it returns the corresponding value.
    """
    def get_candidates(self):
        # Each candidate is a 3-tuple: (person, property_name, value)
        return [
            ("Alice", "age", 25),
            ("Bob", "age", 35),
            ("Charlie", "age", 40)
        ]

# Registry mapping predicate names (as in the AST) to predicate objects.
predicate_registry = {
    "person": PersonPredicate(),
    "enemy": EnemyPredicate(),
    "frenemy": FrenemyPredicate(),
    "get_email": GetEmailPredicate(),
    "get_property": GetPropertyPredicate()

}

def main():
    print("Test KGraph Infer")

    kg_query = """
person(?X), 
not( ( enemy(?X); frenemy(?X) ) ), 
get_email(?X, ?M), 
get_property(?X, 'age', ?Value),
?Age = ?Value,
?Age > 20,
?Total is ( (?Age + 10) / 5),
?Total > 5 + 1,
?X in ['Alice', 'Bob', 'Charlie'],
?P = ['Alice', 'Bob', 'Charlie'],
?Q = [?X],
?Q subset ?P,
?People = collection { ?Person | person(?Person) },
?Sum = sum{ ?N | ?N in [1,1,1,1,1,2,3,4,5] },
?Records =set { 
?Rec | 
person(?Person),
( 
(
get_email(?Person, ?E),
?Rec = [?Person, ?E]
);
(
?Rec = [?Person, 'alice@example.com']
)
)
}.
"""

    infer = KGraphInfer(predicate_registry)

    answer_set = infer.execute(kg_query)

    print(answer_set)

    print("Answers:")

    for answer in answer_set.get_results():
        print(answer)

    # person(?X),
    # get_property(?X, 'age', ?Value),
    # ?Value >= 35,
    # ?L in [1,2,3,4,5],
    # [ ?k = ?v ] in ['key1' = 'value1', 'key2' = 'value2'],
    # ?S subset ['a' = 1, 'b' = 2, 'c' = 3],
    # [ 'a' = 1, 'b' = 5 ] subset ['a' = 1, 'b' = 2, 'c' = 3].
    # [ ?k1 = ?v1, ?k2 = ?v2, ?k3 = ?v3 ] subset ['a' = 1, 'b' = 2, 'c' = 3, 'd' = 4, 'e' = 5, 'f' = 6, 'g' = 7].

    # person(?X),
    # get_property(?X, 'age', ?Value),
    #     ?Value >= 35.

    kg_query = """
    // ?Birth = '1990-01-01'^Date,
    // ?Birth < '2000-01-01'^Date,
    // ?EventTime = '2023-02-18T14:00:00'^DateTime,
    // ?EventTime >= '2023-02-18T00:00:00'^DateTime,
    // ?Start = '08:00:00'^Time,
    // ?End = '17:00:00'^Time,
    // ?Start < ?End,
    // ?Duration = 'PT1H30M'^Duration,
    // ?Duration >= 'PT1H'^Duration,
    // ?Price = '19.99'^Currency(USD),
    // ?Price > '10.00'^Currency(USD),
    // ?Website = 'https://example.com'^URI,
    // ?Website == 'https://example.com'^URI,
    // ?Mass = '100.0'^Unit('http://qudt.org/vocab/unit/kg'),
    // ?Mass > '50.0'^Unit('http://qudt.org/vocab/unit/kg'),
    // ?Location = '40.7128,-74.0060'^GeoLocation,
    // ?Location == '40.7128,-74.0060'^GeoLocation,
    // 'generic string' == 'generic string',
    // 'apple' < 'zebra',
    // 42 > 10.
    
    person(?X),
    get_property(?X, 'age', ?Value),
    // 1 > 2,
    // [1,2,5] != [1,2,3],
    // [ 'k1' = 5 ] > [ 'k2' = 3 ],
    
    [ ?k = ?v ] in ['key1' = 'value1', 'key2' = 'value2'],

    ?Value >= 5,
    ?Value < 40.
"""

    answer_set = infer.execute(kg_query)

    print(answer_set)

    success = answer_set.get_eval_result()

    print(f"Eval result: {success}")

    print("Answers:")

    for answer in answer_set.get_results():
        print(answer)

if __name__ == "__main__":
    main()
