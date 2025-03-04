from kgraphinfer.filter_infer.filter_predicate import FilterPredicate
from kgraphinfer.kgraph_infer import KGraphInfer
from kgraphinfer.parser.kgraph_infer_parser import KGraphInferParser


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
PREDICATE_REGISTRY = {
    "person": PersonPredicate(),
    "enemy": EnemyPredicate(),
    "frenemy": FrenemyPredicate(),
    "get_email": GetEmailPredicate(),
    "get_property": GetPropertyPredicate()

}


def main():
    print("Test KGraph Infer")

    parser = KGraphInferParser()

    kgquery = """
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

    kgquery_parsed = parser.infer_parse(kgquery)

    print(kgquery_parsed)

    evaluator = KGraphInfer(PREDICATE_REGISTRY)

    results = evaluator.run(kgquery_parsed)

    print("Answers:")

    for answer in results:
        print(answer)


if __name__ == "__main__":
    main()
