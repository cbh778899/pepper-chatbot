import json
import os
from collections import defaultdict

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the file paths
input_file_path = os.path.join(current_dir, 'behaviours_merged.json')
output_file_path = os.path.join(current_dir, 'behaviours_described.json')

# Load the JSON data
with open(input_file_path, 'r') as file:
    data = json.load(file)

# Dictionary to hold merged behaviours
merged_behaviours = defaultdict(lambda: {
    "behaviour_variations": [],
    "action_description": "<NO DESCRIPTION>"
})

# Merge behaviours
for item in data:
    for behaviour in item["behaviours"]:
        key = behaviour.split('/')[-1].split('_')[0].lower()
        merged_behaviours[key]["behaviour_variations"].append(behaviour)

# Remove duplicates within lists
for key, value in merged_behaviours.items():
    value["behaviour_variations"] = list(set(value["behaviour_variations"]))

# Convert back to list and sort by the behaviour key
merged_data = [{"behaviour_key": key, **value} for key, value in merged_behaviours.items()]
merged_data = sorted(merged_data, key=lambda x: x["behaviour_key"])

# Save the merged JSON data
with open(output_file_path, 'w') as file:
    json.dump(merged_data, file, indent=4)
