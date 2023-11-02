import maya.cmds as cmds
import sys
import os
basePath = 'C:/HdriHaven'
sys.path.append(basePath)

# Create a new shelf
if not cmds.shelfLayout('PolyHaven', exists=True):
    cmds.shelfLayout('PolyHaven', parent='ShelfLayout')

iconPath = os.path.join(basePath, 'polyhaven.png')
# Add the plugin button to the shelf
cmds.shelfButton(
    parent='PolyHaven',
    image1=iconPath,
    command=("import sys; sys.path.append('" + basePath + "'); import main; main.show_window()"),
    label='Run Python Script',
    annotation='Run Python Script'
)
