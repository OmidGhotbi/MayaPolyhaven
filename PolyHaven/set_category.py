import json
import os
from get_path import getPath

# Prepare and set the categories / subcategories
class getCategories():
    def load_categories(self):
        # Load categories and subcategories from JSON file
        with open(os.path.join(getPath().base_path(), 'asset_cat.json'), 'r') as f:
            data = json.load(f)
        categories = data['categories']
        subcategories = data['subcategories']

        # Create a nested dictionary for the subcategories
        nested_subcategories = {}
        for category, subcats in subcategories.items():
            nested_subcategories[category] = self.create_dict(subcats)

        return categories, nested_subcategories
        
    # Nested dictionary for the subcategories
    def create_dict(self, data):
        result = {}
        for key, value in data.items():
            if key == "root":
                for item in value:
                    result[item] = []
            elif isinstance(value, list):
                result[key] = value
            else:
                result[key] = self.create_dict(value)
        return result