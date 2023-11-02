import json
import os
import sys

basePath = 'C:/HdriHaven'

# Get/Set path to inventory and the current Python script
class getPath():
    def __init__(self):
        # Load the settings from the JSON file
        with open(os.path.join(self.base_path(), 'settings.json'), 'r') as f:
            self.settings = json.load(f)

        # Check if inventoryPath is empty
        if not self.settings["inventoryPath"]:
            # Set inventoryPath to be a subfolder of the current Python path
            self.settings["inventoryPath"] = os.path.join('Inventory')

        # Add the inventory Path to sys.path and save settings
        self.add_path(self.settings["inventoryPath"])
        self.update_settings()

    def update_settings(self, new_path=None):

        # If a new path is provided, update inventoryPath
        if new_path:
            self.settings["inventoryPath"] = new_path

        # Check if the inventoryPath exists
        if not os.path.exists(self.settings["inventoryPath"]):
            # If not, create the directory
            os.makedirs(self.settings["inventoryPath"])
            
        # Update the settings in the JSON file
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
        
        # Update the settings in the JSON file
        with open(os.path.join(self.base_path(), 'settings.json'), 'w') as f:
            json.dump(self.settings, f)

    # Return current Python script path
    def base_path(self):
        return basePath
    
    # Return current inventory path
    def get_inventory_path(self):
        return self.settings["inventoryPath"]
    
    # Add new path to Python system path
    def add_path(self, new_path):
        if new_path not in sys.path:
            sys.path.append(new_path)
    
    # Return current Maya version module path
    def get_maya_module_path(self):
        maya_path = os.getenv('MAYA_LOCATION')
        maya_modul_path = os.path.join(maya_path, 'Python/Lib/site-packages/pip/_vendor')
        return maya_modul_path
