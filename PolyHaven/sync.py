from PySide2.QtCore import QThread, Signal
import os
import json
from get_path import getPath
import requests

# Sync background thread
class SyncThread(QThread):
    progress = Signal(int)

    def __init__(self):
        super().__init__()
        self.session = requests.Session()

    def run(self):
        # URL of the API
        url = "https://api.polyhaven.com/assets?t=all"
        
        # Send a GET request to the API
        response = self.session.get(url)
        
        # Convert the response to JSON
        data = response.json()

        path = getPath().get_inventory_path()
        
        # Path where the JSON data will be saved
        json_file_path = os.path.join(path, "data.json")
        
        # Save the JSON data to the file
        with open(json_file_path, 'w') as f:
            json.dump(data, f)
        
        # Get the total number of items to sync
        total_items = len(data)

        # Loop through each item in the data
        for i, item in enumerate(data):
            # Update the progress bar
            self.progress.emit((i + 1) / total_items * 100)

            # Get the name and type of the item
            name = item

            # Create a directory for the item if it doesn't exist
            directory = os.path.join(path, name)
            if not os.path.exists(directory):
                os.makedirs(directory)
        
            # URL of the image base on item name
            image_url = f"https://cdn.polyhaven.org/asset_img/thumbs/{name}.png?width=256&height=256"
        
            # Path where the image will be saved
            file_path = os.path.join(directory, f"{name}.png")
            
            # Send a GET request to the image URL
            if not os.path.isfile(file_path):
                image_response = self.session.get(image_url)
        
                # Save the image to the directory
                with open(file_path, 'wb') as f:
                    f.write(image_response.content)
            
            # URL of the JSON file
            json_url = f"https://api.polyhaven.com/files/{name}"
            
            # Path where the JSON file will be saved
            json_file_path = os.path.join(directory, f"{name}.json")
            
            # Check if the JSON file already exists
            if not os.path.isfile(json_file_path):
                # If not, send a GET request to the JSON URL
                json_response = self.session.get(json_url)
                
                # Save the JSON file to the directory
                with open(json_file_path, 'w') as f:
                    json.dump(json_response.json(), f)
