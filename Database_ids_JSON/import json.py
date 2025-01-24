import json

# Load the JSON file to analyze the titles
file_path = './pièces.json'
with open(file_path, 'r') as file:
    data = json.load(file)

# Count the number of titles with more than 15 characters
count = sum(1 for piece in data["pièces"] if len(piece["titre"]) > 20)
count