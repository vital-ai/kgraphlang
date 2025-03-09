from abc import ABC, abstractmethod
from kgraphlang.kgraph_infer import UNBOUND
from kgraphlang.predicate.kgraph_predicate import KGraphPredicate
from datasketch import MinHash, MinHashLSH
from datasketch import MinHashLSHForest
from rapidfuzz import fuzz

def get_minhash(name):
    m = MinHash(num_perm=128)
    for token in name:
        m.update(token.encode('utf8'))
    return m

def find_closest_strings(query_string, index, ids_to_names, top_k=10, min_score=0):
    """
    Given a query string, return the top_k closest matches whose fuzzy similarity
    is at least min_score.
    """
    query_hash = get_minhash(query_string)
    result_ids = index.query(query_hash)
    scored_results = []

    for rid in result_ids:
        name = ids_to_names[str(rid)]

        # different scoring options
        # this one should be good for personal name partial matches
        # similarity_score = fuzz.WRatio(name, query_string)

        # this is more for partial substring matches
        similarity_score = fuzz.partial_ratio(name, query_string)


        scored_results.append((rid, name, similarity_score))

    scored_results.sort(key=lambda x: x[2], reverse=True)

    # Optionally filter results below min_score
    if min_score:
        scored_results = [r for r in scored_results if r[2] >= min_score]

    return scored_results[:top_k]

class FilterStringHashPredicate(KGraphPredicate, ABC):

    # the input data is arity 2:
    # id, string value to index

    # the predicate is arity 3:
    # query string
    # matching id
    # matching score

    # optional annotations:
    # top_k
    # min_score

    def __init__(self, *, data: list[tuple]):
        super().__init__()
        self.data = data
        self.lsh_index = MinHashLSH(threshold=0.1, num_perm=128)

        ids_to_names = {}

        for id, name in data:
            minhash = get_minhash(name)
            print(f"Adding {id}: '{name}' : '{minhash}'")
            ids_to_names[str(id)] = name
            self.lsh_index.insert(str(id), minhash)

        self.ids_to_names = ids_to_names

    def get_arity(self) -> int:
        return 3

    # highest score is best
    def get_annotation_ids(self) -> list:
        return ["top_k", "min_score"]

    def eval_impl(self, *, input_dict: dict, annotations: list = None) -> list:

        results = []

        print(input_dict)

        # TODO
        # enforce query must be bound
        # handle case when match id and score are bound
        query = input_dict.get(0)
        match_id = input_dict.get(1)
        match_score = input_dict.get(2)

        top_k = 10
        min_score = 0

        # Extract annotation values if provided
        if annotations:
            for ann in annotations:
                # Each annotation is expected to be in the form: (name, [arg1, ...])
                if ann[0] == "top_k" and ann[1]:
                    try:
                        top_k = int(ann[1][0])
                    except Exception as e:
                        print(f"Invalid top_k annotation: {ann[1]}")
                elif ann[0] == "min_score" and ann[1]:
                    try:
                        min_score = float(ann[1][0])
                    except Exception as e:
                        print(f"Invalid min_score annotation: {ann[1]}")

        scored_results = find_closest_strings(query, self.lsh_index, self.ids_to_names, top_k=top_k, min_score=min_score)

        print(f"Top matches for '{query}':")
        for rid, match, score in scored_results:
            print(f"Match: {match} (id={rid}) Score: {score:.4f}")
            results.append({0: query, 1: rid, 2: round(float(score), 4)})

        return results
