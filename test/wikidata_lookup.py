import json
import time
# {"kind": "entity", "id": "/m/010016", "properties": {"alternatives": ["Denton, Texas"], "description": "city in Texas, United States", "label": "Denton", "wikidata_id": "Q128306", "wikipedia": "https://en.wikipedia.org/wiki/Denton,_Texas"}}
from urllib.error import HTTPError
import sys
from SPARQLWrapper import SPARQLWrapper, JSON

# fiddling with fb15k dataset while figuring out labels of types


# Define a mapping from our high-level (natural) entity categories to Wikidata Q-IDs.
# (You can adjust these as needed.)
TOP_LEVEL_MAPPING = {
    "Person": ["Q5", "Q483394"],
    "Organization": ["Q43229"],
    "Location": ["Q2221906"],
    "Event": ["Q1656682"],
    "Creative Work": ["Q838948"],
    "Sport": ["Q349"],
    "Award": ["Q19020"],
    "Educational Institution": ["Q2385804"],
    "Academic Field": ["Q11862829"],
    "Government/Political Entity": ["Q7278"],
    "Medical Condition": ["Q12136"],
    "Media/Online Content": ["Q328"],
    "Business/Economic Entity": ["Q4830453"],
    "Animal": ["Q144"],
    "Language": ["Q34770"],
    "Musical Instrument": ["Q34379", "Q35120"],
    "Physical Object": ["Q223557"]
}


PRIORITY_ORDER = [
    "Person",
    "Organization",
    "Location",
    "Event",
    "Creative Work",
    "Educational Institution",
    "Government/Political Entity",
    "Business/Economic Entity",
    "Sport",
    "Award",
    "Medical Condition",
    "Language",
    "Musical Instrument",
    "Physical Object",
    "Academic Field"
]

# SPARQL endpoint for Wikidata
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


def safe_query(query, max_retries=50, pause_secs=10):
    """
    Execute a SPARQL query with a retry mechanism if HTTP Error 429 is encountered.
    """
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    attempt = 0
    while attempt < max_retries:
        try:
            return sparql.query().convert()
        except HTTPError as e:
            if e.code == 429:
                attempt += 1
                print(
                    f"HTTP Error 429 encountered. Pausing for {pause_secs} seconds before retrying... (Attempt {attempt}/{max_retries})",
                    file=sys.stderr)
                time.sleep(pause_secs)
            else:
                print(f"HTTP Error {e.code} encountered: {e}", file=sys.stderr)
                sys.exit(1)
    print("Max retries exceeded. Exiting.", file=sys.stderr)
    sys.exit(1)

def get_ancestors(wd_id):
    """
    Query Wikidata for ancestor types using a UNION of:
      - Direct P31 (instance of) and its subclass chain (P279).
      - The subclass chain (P279) starting from the entity itself.
    Returns a set of ancestor QIDs (as strings), excluding the input wd_id.
    """
    query = f"""
    SELECT ?ancestor WHERE {{
      {{
        wd:{wd_id} wdt:P31 ?instance .
        ?instance (wdt:P279)* ?ancestor .
      }}
      UNION
      {{
        wd:{wd_id} (wdt:P279)* ?ancestor .
      }}
    }}
    """
    results = safe_query(query)
    ancestors = set(uri.split("/")[-1] for uri in (result["ancestor"]["value"] for result in results["results"]["bindings"]))
    # Remove the input wd_id from the ancestor set
    ancestors.discard(wd_id)
    return ancestors

def classify_entity(wd_id):
    """
    Given a Wikidata ID, fetch its ancestor types and determine which top-level categories
    it belongs to based on TOP_LEVEL_MAPPING. Returns a tuple: (list of matching categories, ancestor set).
    """
    ancestors = get_ancestors(wd_id)
    matching_categories = []
    for category, top_qids in TOP_LEVEL_MAPPING.items():
        for top_qid in top_qids:
            if top_qid in ancestors:
                matching_categories.append(category)
                break
    # Apply priority: if any high-priority category is found, choose the first one in PRIORITY_ORDER.
    for cat in PRIORITY_ORDER:
        if cat in matching_categories:
            matching_categories = [cat]
            break
    return matching_categories, ancestors

def main():

    # wd_id = "Q207405"
    # categories, ancestors = classify_entity(wd_id)
    # print(f"Categories: {categories}")
    # print(f"Ancestors: {ancestors}")
    # exit(0)

    input_filename = "../test_data/FB15k/output.jsonl"
    output_filename = "../test_data/FB15k/output_with_categories.jsonl"

    with open(input_filename, 'r', encoding='utf-8') as infile, \
            open(output_filename, 'w', encoding='utf-8') as outfile:
        line_number = 0

        for line in infile:

            line_number += 1

            if line_number % 1000 == 0:
                print(f"processing line: {line_number}")

            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_number}: {e}", file=sys.stderr)
                sys.exit(1)


            properties = data.get("properties", {})
            wikidata_id = properties.get("wikidata_id")
            if not wikidata_id:
                print(f"No wikidata_id found for line {line_number}", file=sys.stderr)
                # sys.exit(1)
                continue

            # print(f"{line_number}: {data}")

            categories, ancestors = classify_entity(wikidata_id)

            time.sleep(0.05)

            if not categories:
                print(
                    f"Error: No matching top-level categories found for wikidata_id {wikidata_id} on line {line_number}",
                    file=sys.stderr)
                print(data)
                print(f"Ancestors found: {ancestors}", file=sys.stderr)
                continue
                # sys.exit(1)


            # Add the mapped categories to the original data
            data["mapped_categories"] = categories
            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()