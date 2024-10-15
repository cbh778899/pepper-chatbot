import json
from collections import defaultdict

# Load the JSON data
with open('/home/sgriff/pepper/pepper-chatbot/src/behaviours.json', 'r') as file:
    data = json.load(file)

# Dictionary to hold merged behaviours
merged_behaviours = defaultdict(lambda: {
    "behaviours": [],
    "input_keywords": [],
    "output_keywords": [],
    "chatbot_response": True
})

# Merge behaviours
for item in data:
    key = tuple(sorted(item["input_keywords"]))
    merged_behaviours[key]["behaviours"].extend(item["behaviours"])
    merged_behaviours[key]["input_keywords"].extend(item["input_keywords"])
    merged_behaviours[key]["output_keywords"].extend(item["output_keywords"])
    merged_behaviours[key]["chatbot_response"] = item["chatbot_response"]

# Remove duplicates within lists
for key, value in merged_behaviours.items():
    value["behaviours"] = list(set(value["behaviours"]))
    value["input_keywords"] = list(set(value["input_keywords"]))
    value["output_keywords"] = list(set(value["output_keywords"]))

# Convert back to list
merged_data = list(merged_behaviours.values())

# Save the merged JSON data
with open('/home/sgriff/pepper/pepper-chatbot/src/behaviours_merged.json', 'w') as file:
    json.dump(merged_data, file, indent=4)
