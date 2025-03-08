import csv
import logging
import hnswlib
import numpy as np
from vital_ai_vitalsigns.embedding.embedding_model import EmbeddingModel


# fiddling with indexing type names


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting the vector index for fb15k types")

    types = []
    descriptions = []
    csv_file = '../test_data/FB15k/fb15k_types.csv'
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming CSV headers are "type" and "description"
            types.append(row['type'].strip())
            descriptions.append(row['description'].strip())

    logging.info(f"Loaded {len(types)} types from {csv_file}")

    embedder = EmbeddingModel()
    vectors_list = embedder.vectorize(descriptions)
    vectors = np.array(vectors_list)
    dimension = vectors.shape[1]
    logging.info(f"Created embeddings with dimension: {dimension}")

    index = hnswlib.Index(space='cosine', dim=dimension)
    index.init_index(max_elements=len(vectors), ef_construction=200, M=16)
    index.add_items(vectors)
    index.set_ef(50)  # ef should be > k for query performance

    logging.info("HNSW index built and items added.")

    # Step 4: Define some query examples to search for similar types
    queries = [
        "Award category",
        "Team position for a player in sports",
        "cities",
        "business"
    ]

    for query in queries:
        query_vector = np.array(embedder.vectorize([query]))
        labels, distances = index.knn_query(query_vector, num_threads=1, filter=None, k=10)

        print(f"\nQuery: '{query}'")
        for rank, (label, distance) in enumerate(zip(labels[0], distances[0])):
            # Ensure that the label is a valid index in our data lists.
            if label < len(types):
                print(f"  Rank {rank + 1}:")
                print(f"    Type: {types[label]}")
                print(f"    Description: {descriptions[label]}")
                print(f"    Similarity Score: {distance:.4f}")
            else:
                print(f"  Rank {rank + 1}: No valid type found, Score: {distance:.4f}")


if __name__ == "__main__":
    main()
