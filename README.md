# Poly Haven Assets Add-on for Maya

A Blender add-on to integrate our assets natively in the Autodesk Maya.

![Screenshot](/Screenshot.jpg)

## Features

1. Download all assets from [Poly Haven](https://polyhaven.com/), and list them under their respective categories in the Asset Browser.
2. Select between Phong and aiArnoldSurfce material
3. Lets you swap the resolution of an asset to higher/lower resolutions any time after import (most are at least 8K).
4. Set the texture mapping scale to the correct real-world size according to the surfaces you've applied it to.
6. Automatic setup of HDRi Light
7. Automatic setup of texture displacement with adaptive subdivision.
8. Automatic import of models and set Materials and texture nodes.

## Installation

1. Download the ZIP file [download it here for free](https://github.com/OmidGhotbi/polyhavenassets/releases/download/release/PolyHaven-v0.0.17-beta.1.zip).
2. Choose one of the following steps as you prefer. **(you do not need to do all of them just one of them would be enough)**

    * a. Unzip the Download release in C:\ for Windows user or ~/ for Mac or Linux user. The final path will be like this **C:\PolyHave**
    * b. Unzip the Download anywhere you want and run Setup.bat in Windows or Setup.sh in Mac or Linux. Setup will do all the necessary changes for you. **Prefered Method**
    * c. Alternatively, you can unzip the download file anywhere you want and add its path in Maya Additional script paths

3. Drag and drop **shelf.py** into Maya viewport, now you have **Polyhaven** shelf in Maya,

Enjoy it

For more detailed instructions, I will add a video tutorial very soon.

## Usage

> A more detailed user guide and video demo will be available soon

1. Open the Polyhaven asset manager by clicking on the PolyHave icon in Maya Shelf.
2. If you run asset manager for the first time Click on the **Sync** button to download the list of available objects, materials, and HDRis
3. Open the asset browser editor and select the Poly Haven library at the top left.
4. Choose the quality that you want to items be Downloaded in the Preview panel on the right side. it's 1k by default.
5. You can download any items by right-clicking and choosing the ***Download*** button in the asset browser menu or selecting the item and clicking on the ***Download*** button in the preview panel.
6. Now the item is available, simply right-click on the item and add the assets to your scene.
7. PolyHaven will release new assets almost daily, so you can click that *Sync* button any time to download new assets.


## Settings
You can change the **Inventory Path** as you wish by go to **Settings** and choose **Set inventory Path** then select a new path

## Known Issues

1. Some Objects may not be imported correctly because of the incorrect FBX on the PolyHaven website.
2. Download All is disabled by default as downloading all of the models, materials, and HDRIs can take up huge space.
