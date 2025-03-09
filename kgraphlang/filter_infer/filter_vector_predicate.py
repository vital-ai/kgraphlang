from abc import ABC, abstractmethod
import logging
import numpy as np
from vital_ai_vitalsigns.embedding.embedding_model import EmbeddingModel
from kgraphlang.kgraph_infer import UNBOUND
from kgraphlang.predicate.kgraph_predicate import KGraphPredicate
import hnswlib

class FilterVectorPredicate(KGraphPredicate, ABC):

    # the input data is arity 2:
    # id, string value to vectorize

    # the predicate is arity 3:
    # query string
    # matching id
    # matching score

    # optional annotations:
    # top_k
    # max_score

    def __init__(self, *, data: list[tuple]):
        super().__init__()
        self.data = data

        descriptions = []
        ids = []

        for vector_id, vector_description in data:
            ids.append(vector_id)
            descriptions.append(vector_description)

        self.embedder = EmbeddingModel()
        vectors_list = self.embedder.vectorize(descriptions)
        vectors = np.array(vectors_list)
        dimension = vectors.shape[1]
        logging.info(f"Created embeddings with dimension: {dimension}")

        index = hnswlib.Index(space='cosine', dim=dimension)
        index.init_index(max_elements=len(vectors), ef_construction=200, M=16)
        index.add_items(vectors)
        index.set_ef(50)  # ef should be > k for query performance
        self.index = index
        self.ids = ids
        self.descriptions = descriptions


    def get_arity(self) -> int:
        return 3

    # lowest score is best
    def get_annotation_ids(self) -> list:
        return ["top_k", "max_score"]

    def eval_impl(self, *, input_dict: dict, annotations: list = None) -> list:

        results = []

        print(input_dict)

        # TODO
        # enforce query must be bound
        # handle case when match id and score are bound
        query = input_dict.get(0)
        match_id = input_dict.get(1)
        match_score = input_dict.get(2)

        query_vector = np.array(self.embedder.vectorize([query]))
        labels, distances = self.index.knn_query(query_vector, num_threads=1, filter=None, k=10)

        print(f"\nQuery: '{query}'")

        for rank, (label, distance) in enumerate(zip(labels[0], distances[0])):
            if label < len(self.ids):
                print(f"  Rank {rank + 1}:")
                print(f"    Type: {self.ids[label]}")
                print(f"    Description: {self.descriptions[label]}")
                print(f"    Similarity Score: {distance:.4f}")
                results.append({0: query, 1: self.ids[label], 2: round(float(distance), 4)})
            else:
                print(f"  Rank {rank + 1}: No valid type found, Score: {distance:.4f}")

        return results

