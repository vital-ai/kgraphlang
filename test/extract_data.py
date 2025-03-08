import logging
import os
import json

# fiddling with test data

logging.basicConfig(level=logging.INFO)

# Define the directory containing the dataset files.
DATA_DIR = "/Users/hadfield/Local/external-git/datasets_knowledge_embedding/FB15k-237"

# File names
TRIPLE_FILES = ["train.txt", "valid.txt", "test.txt"]
ENTITY_MAPPING_FILE = "entity2wikidata.json"
OUTPUT_FILE = "output.jsonl"
FLORA_OUTPUT_FILE = "output.flr"


def escape_val(s):
    # Escape single quotes in a string.
    return s.replace("'", "\\'")


# Function to load entity mapping from JSON file.
def load_entity_mapping(path):
    with open(path, "r", encoding="utf-8") as f:
        entity_map = json.load(f)
    return entity_map


# Function to read triples from a file.
def load_triples(file_path):
    triples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Assuming each line is tab-separated: subject \t relation \t object
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue
            subj, rel, obj = parts
            triples.append((subj, rel, obj))
    return triples

def format_entity_frame(urn, props):
    """
    Format an entity as a Flora-2 frame:
    ('<URN>'[prop1->'value1', prop2->'value2', ...]).
    Only include a property if it exists.
    """
    frame_props = []
    if "label" in props and props["label"]:
        frame_props.append(f"label->'{escape_val(props['label'])}'")
    if "description" in props and props["description"]:
        frame_props.append(f"description->'{escape_val(props['description'])}'")
    if "alternatives" in props and props["alternatives"]:
        alts = props["alternatives"]
        alts_str = "[" + ", ".join(f"'{escape_val(alt)}'" for alt in alts) + "]"
        frame_props.append(f"alternatives->{alts_str}")
    if "wikidata_id" in props and props["wikidata_id"]:
        frame_props.append(f"wikidata_id->'{escape_val(props['wikidata_id'])}'")
    if "wikipedia" in props and props["wikipedia"]:
        frame_props.append(f"wikipedia->'{escape_val(props['wikipedia'])}'")
    props_str = ", ".join(frame_props)
    # Produce frame: ('<URN>'[...]).
    return f"('{urn}'[{props_str}])."

def format_relationship_frame(rel_urn, source, rel_type, destination):
    """
    Format a relationship as a Flora-2 frame:
    ('<rel_urn>'[source->'<source>', type->'<rel_type>', destination->'<destination>']).
    """
    return (f"('{rel_urn}'[source->'{source}', type->'{escape_val(rel_type)}', "
            f"destination->'{destination}']).")


def main():
    # Load the entity mapping JSON (if it exists).
    entity_mapping_path = os.path.join(DATA_DIR, ENTITY_MAPPING_FILE)
    if os.path.exists(entity_mapping_path):
        entities = load_entity_mapping(entity_mapping_path)
    else:
        entities = {}

    # Initialize relationships list.
    relationships = []

    # Process all triple files.
    for filename in TRIPLE_FILES:
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        triples = load_triples(file_path)
        for subj, rel, obj in triples:
            # Add the relationship.
            relationships.append({
                "source": subj,
                "destination": obj,
                "type": rel
            })
            # Make sure the subject is in our entity dict.
            if subj not in entities:
                entities[subj] = {}  # Empty dictionary if no mapping info.
            # Make sure the object is in our entity dict.
            if obj not in entities:
                entities[obj] = {}

    # Now prepare output: First, a list of entities with "kind": "entity"
    # We create one dict per line that includes the id and its properties.
    output_lines = []
    for ent_id, props in entities.items():
        # Create a record for the entity.
        # For clarity, we include the key "id" and all properties.
        record = {
            "kind": "entity",
            "id": ent_id,
            "properties": props
        }
        output_lines.append(record)

    # Then, add each relationship as its own record.
    for rel in relationships:
        record = {
            "kind": "relationship",
            "source": rel["source"],
            "destination": rel["destination"],
            "type": rel["type"]
        }
        output_lines.append(record)

    # Write out to a JSONNL file (one JSON object per line)
    output_path = os.path.join(DATA_DIR, OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in output_lines:
            json_line = json.dumps(record)
            f.write(json_line + "\n")

    print(f"Output written to {output_path}")

    # Generate Flora-2 (.flr) output.
    flora_lines = []
    # For entities.
    for ent_id, props in entities.items():
        urn = f"urn:{ent_id}"  # Convert entity ID to URN.
        frame = format_entity_frame(urn, props)
        flora_lines.append(frame)

    # For relationships.
    for idx, rel in enumerate(relationships, start=1):
        rel_urn = f"urn:rel/{idx}"
        source_urn = f"urn:{rel['source']}"
        dest_urn = f"urn:{rel['destination']}"
        frame = format_relationship_frame(rel_urn, source_urn, rel["type"], dest_urn)
        flora_lines.append(frame)

    flora_out_path = os.path.join(DATA_DIR, FLORA_OUTPUT_FILE)
    with open(flora_out_path, "w", encoding="utf-8") as f:
        for line in flora_lines:
            f.write(line + "\n")
    logging.info(f"Flora-2 output written to {flora_out_path}")


if __name__ == "__main__":
    main()
