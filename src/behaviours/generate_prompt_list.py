import json
import os

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the file paths
json_file_path = os.path.join(current_dir, 'behaviours_described.json')
output_file_path = os.path.join(current_dir, 'behaviours_list.txt')

# Load the JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# List to hold the formatted behaviours
formatted_behaviours = []

# Process each behaviour
for item in data:
    behaviour_key = item["behaviour_key"]
    description = item["action_description"]
    if description != "<NO DESCRIPTION>":
        formatted_behaviours.append(f'"{behaviour_key}" - {description}')
    else:
        formatted_behaviours.append(f'"{behaviour_key}"')

# Save the formatted behaviours to a file
with open(output_file_path, 'w') as file:
    for behaviour in formatted_behaviours:
        file.write(f'{behaviour}\n')
