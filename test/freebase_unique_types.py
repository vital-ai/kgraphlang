import csv
from collections import Counter


input_csv_filename = "../test_data/type_output.csv"  # change to your file's name if different

output_csv_filename = "../test_data/type_count.csv"   # Output CSV with type and count


unique_third_column = set()


# Use a Counter to count occurrences of the third column values
counter = Counter()

with open(input_csv_filename, "r", encoding="utf-8") as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
        if len(row) >= 3:  # Ensure there is a third column
            counter[row[2]] += 1

# Sort the items by count in descending order
sorted_counts = sorted(counter.items(), key=lambda x: x[1], reverse=True)

# Write the sorted counts to the output CSV file
with open(output_csv_filename, "w", encoding="utf-8", newline="") as out_file:
    writer = csv.writer(out_file)
    # Write header
    writer.writerow(["type", "count"])
    # Write each type and its count
    for type_value, count in sorted_counts:
        writer.writerow([type_value, count])

print("Done! The unique types and their counts have been written to", output_csv_filename)
