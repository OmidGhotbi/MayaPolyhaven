from PySide2.QtCore import QThread, Signal
import os
import json
import requests
from enum import Enum
from get_path import getPath

# Create a session
session = requests.Session()

# Categories enum
class cat(Enum):
    HDRIs = 0
    Textures = 1
    Models = 2

# Define download thread class
class DownloadThread(QThread):
    progress = Signal(int)

    # Initialize variables
    def __init__(self, category, item_name, quality):
        QThread.__init__(self)
        self.category = category
        self.item_name = item_name
        self.quality = quality

    def run(self):
        path = getPath().get_inventory_path()
        # Construct the path to the JSON file
        json_file_path = os.path.join(path, self.item_name, self.item_name + '.json')

        # Load the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        root =  None
        # Get the download URLs based on the category and quality
        if self.category.value == cat.Models.value:
            root = 'fbx'
            downloads = data[root][self.quality]
        elif self.category.value == cat.Textures.value:
            root = 'blend'
            downloads = data[root][self.quality]
        elif self.category.value == cat.HDRIs.value:
            root = 'hdri'
            downloads = data[root][self.quality]

        # Initialize variables to keep track of the total size of all files
        total_files = sum(1 for key, value in downloads.items() if 'include' in value for filename, file_info in value['include'].items() if 'url' in file_info)
        downloaded_files = 0

        # Download all the files
        for key, value in downloads.items():
            subpath = 'Textures'
            download_path = None
            # Check if 'url' is in value and download the file
            if 'url' in value and ('fbx' in key or 'hdr' in key):
                total_files += 1
                download_url = value['url']
                # Construct the path to save the downloaded file
                if root == 'fbx':
                    download_path = os.path.join(path, self.item_name, self.item_name + '_' + self.quality + '.fbx')
                else:
                    download_path = os.path.join(path, self.item_name, self.item_name + '_' + self.quality + '.hdr')
                    print(download_url)

                # Download the file if the file not exists
                if not os.path.exists(download_path):
                    response = session.get(download_url, stream=True)
                    if response.status_code == 200:
                        with open(download_path, 'wb') as f:
                            for chunk in response.iter_content(8192):
                                f.write(chunk)

                        # Update UI
                        downloaded_files += 1
                        progress_percentage = (downloaded_files / total_files) * 100
                        self.progress.emit(progress_percentage)
                else:
                    # Update UI
                    downloaded_files += 1
                    progress_percentage = (downloaded_files / total_files) * 100
                    self.progress.emit(progress_percentage)
                    
            # Check if 'include' exists in value and contains any files, then download the files.
            if 'include' in value:
                for filename, file_info in value['include'].items():
                    if 'url' in file_info:
                        download_url = file_info['url']
                        # Construct the path to save the downloaded file
                        if root == 'fbx' or root == 'blend':
                            download_path = os.path.join(path, self.item_name, subpath)
                        else:
                            download_path = os.path.join(path, self.item_name)
                        
                        if not os.path.exists(download_path):
                            os.makedirs(download_path)
                        
                        final_path = os.path.join(download_path, filename.split('/')[-1])

                        # Download the file if the file not exists
                        if not os.path.exists(final_path):
                            response = session.get(download_url, stream=True)
                            if response.status_code == 200:
                                with open(final_path, 'wb') as f:
                                    for chunk in response.iter_content(8192):
                                        f.write(chunk)

                                # Update UI
                                downloaded_files += 1
                                progress_percentage = (downloaded_files / total_files) * 100
                                self.progress.emit(progress_percentage)
                        else:
                            # Update UI
                            downloaded_files += 1
                            progress_percentage = (downloaded_files / total_files) * 100
                            self.progress.emit(progress_percentage)