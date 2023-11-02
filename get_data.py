import os
import json
from get_path import getPath

# Load saved data from local json
def load_data():
    # Path where the JSON data is saved
    path = getPath().get_inventory_path()
    json_file_path = os.path.join(path, "data.json")
    
    # Check if the JSON file exists
    if os.path.isfile(json_file_path):
        # If it exists, load the data from the file
        with open(json_file_path, 'r') as f:
            return json.load(f)
    
    return None