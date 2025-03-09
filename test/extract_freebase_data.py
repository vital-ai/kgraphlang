import json
import csv

# Step 1: Parse the JSONL file and collect all freebase ids
ids = {}

jsonl_filename = "../test_data/FB15k/output-1.jsonl"

with open(jsonl_filename, "r", encoding="utf-8") as jsonl_file:
    for line in jsonl_file:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            if record.get("kind") == "entity":
                freebase_id = record.get("id")
                if freebase_id:
                    ids[freebase_id] = True
        except json.JSONDecodeError:
            print("Skipping invalid JSON line.")
            continue

print(f"Collected {len(ids)} freebase ids.")

data_dir = "/Users/hadfield/Library/CloudStorage/GoogleDrive-marc@vital.ai/My Drive/freebase/idirlab-freebases/Metadata/"

# Step 2: Read the CSV file line by line and output matching rows
csv_input_filename = data_dir + "object_types.csv"  # adjust filename as needed
csv_output_filename = "../test_data/type_output.csv"  # output file

with open(csv_input_filename, "r", encoding="utf-8") as csv_in, \
        open(csv_output_filename, "w", encoding="utf-8", newline="") as csv_out:
    csv_reader = csv.reader(csv_in)
    csv_writer = csv.writer(csv_out)

    # Optionally write header if your CSV has one; for now, we'll assume no header.
    for row in csv_reader:
        if len(row) < 2:
            continue  # skip rows that don't have at least 2 columns
        # Check if first column is in our freebase id map and second column equals '/type/object/type'
        if row[0] in ids and row[1] == "/type/object/type":
            csv_writer.writerow(row)

print("Processing complete. Matching rows written to", csv_output_filename)
