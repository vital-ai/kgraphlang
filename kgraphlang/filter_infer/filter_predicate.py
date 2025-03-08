from abc import ABC, abstractmethod

from kgraphlang.kgraph_infer import UNBOUND
from kgraphlang.predicate.kgraph_predicate import KGraphPredicate


class FilterPredicate(KGraphPredicate, ABC):
    """
    A Predicate subclass that handles filtering against a fixed candidate set.
    Subclasses should implement get_candidates() to return a list of candidate tuples.
    The eval_impl() method provided here filters the candidate tuples based on the
    provided input dictionary.
    """
    @abstractmethod
    def get_candidates(self) -> list:
        """
        Return a list of candidate tuples.
        Each candidate is a tuple of concrete values.
        """
        pass

    def eval_impl(self, input_dict: dict) -> list:
        results = []
        for candidate in self.get_candidates():
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

