import csv
import logging
from kgraphlang.filter_infer.filter_string_hash_predicate import FilterStringHashPredicate
from kgraphlang.filter_infer.filter_vector_predicate import FilterVectorPredicate
from kgraphlang.kgraph_infer import KGraphInfer


class TypePredicate(FilterVectorPredicate):
    pass

class TypeStringHash(FilterStringHashPredicate):
    pass

# id, property, value
class EntityPropertyPredicate(FilterVectorPredicate):
    pass

# source id, destination id, relation type
class EntityRelationPredicate(FilterVectorPredicate):
    pass


def do_query(predicate_registry, kg_query):

    infer = KGraphInfer(predicate_registry)

    answer_set = infer.execute(kg_query)

    print(answer_set)

    print("Answers:")

    for answer in answer_set.get_results():
        print(answer)

def main():
    logging.basicConfig(level=logging.INFO)

    type_data: list[tuple[str,str]] = []

    # these are entity to entity relation types

    csv_file = '../test_data/FB15k/fb15k_types.csv'

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:

            # use name as id
            type_name = row['type'].strip()
            type_description = row['description'].strip()

            type_data.append( (type_name, type_description) )


    relation_type_vector_predicate = TypePredicate(data=type_data)

    relation_type_string_hash_predicate = TypeStringHash(data=type_data)

    # TODO entity types using dataset (not wikidata assigned ones)

    # entity types by string hash name
    # entity types by vector

    # entity search by list of types
    # find hockey teams

    # entity search by name
    # find names with "Fred"

    # entity search by name and list of types
    # find named with "Middletown" and city type
    # find "Princeton" and university type

    # predicate for entity properties, read in from jsonl file
    # use filter case

    # predicate for entity to entity relations (edges) from jsonl file
    # use filter case

    # currently no other properties in the relations (edges) besides
    # source, destination, and type

    entity_property_predicate = EntityPropertyPredicate(data=[])

    entity_relation_predicate = EntityRelationPredicate(data=[])

    predicate_registry = {
        "relation_type_vector": relation_type_vector_predicate,
        "relation_type_string_hash": relation_type_string_hash_predicate,
        "entity_property": entity_property_predicate,
        "entity_relation": entity_relation_predicate,
    }

    kg_query = "type_vector('Sports', ?vector_match_id, ?vector_match_score)."

    do_query(predicate_registry, kg_query)

    kg_query = "type_string_hash('Ceremony', ?string_hash_match_id, ?string_hash_match_score)."

    do_query(predicate_registry, kg_query)


if __name__ == "__main__":
    main()
