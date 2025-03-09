from abc import ABC, abstractmethod
from kgraphlang.kgraph_infer import UNBOUND
from kgraphlang.predicate.kgraph_predicate import KGraphPredicate


class FilterPredicate(KGraphPredicate, ABC):
    """
    A Predicate subclass that handles filtering against a fixed candidate set
    defined when the predicate is constructed.
    The eval_impl() method provided here filters the candidate tuples based on the
    provided input dictionary.
    """

    def __init__(self, *, data: list[tuple]):
        super().__init__()
        self.data = data

    def get_arity(self) -> int:
        return len(self.data[0])

    def get_annotation_ids(self) -> list:
        return []

    def eval_impl(self, *, input_dict: dict, annotations: list = None) -> list:

        if annotations is not None and len(annotations) > 0:
            print(f"Annotations: {annotations}")

        results = []

        for candidate in self.data:
            consistent = True
            for i, val in enumerate(candidate):
                # If the input value is bound, candidate value must match.
                if input_dict.get(i) is not UNBOUND and input_dict.get(i) != val:
                    consistent = False
                    break
            if consistent:
                # Return a dictionary mapping each parameter index to its candidate value.
                results.append({i: candidate[i] for i in range(len(candidate))})
        return results

