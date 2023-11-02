import os
import json
import maya.cmds as cmds
from enum import Enum
from get_path import getPath
from download import DownloadThread
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QMainWindow, QPushButton, QProgressBar

# Categories enum
class cat(Enum):
    HDRIs = 0
    Textures = 1
    Models = 2

# Custon menu and button class
class popbutton(QtWidgets.QPushButton):
    def __init__(self, category, item_name, quality, window, *args, **kwargs):
        super(popbutton, self).__init__(*args, **kwargs)
        self.category = category
        self.name = item_name
        self.quality = quality
        self.window = window  # assign the passed window instance
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

        # Create an instance of Window
        #self.window = Window()
    
    # Update quality if changed
    def update_quality(self, new_quality):
        self.quality = new_quality

    # Assign the proper function to every item
    def show_menu(self, pos):
        menu = QtWidgets.QMenu()
        action1 = None
        if self.category.value == cat.HDRIs.value:
            action1 = menu.addAction("Create HDRIs Light")
            action1.triggered.connect(self.create_HDRI_light)
        elif self.category.value == cat.Textures.value:
            action1 = menu.addAction("Assign to object phong")
            action3 = menu.addAction("Assign to object Arnold")
            action1.triggered.connect(self.assign_texture)
            action3.triggered.connect(self.assign_texture_arnold)
        elif self.category.value == cat.Models.value:
            action1 = menu.addAction("Add Models to the scene")
            action1.triggered.connect(self.import_model)
        action2 = menu.addAction("Download")
        
        action = menu.exec_(self.mapToGlobal(pos))
        if action == action2:
            self.download_item()
    
    
    # Call download in background thread
    def download_item(self):
        self.window.progress_bar.setValue(0)
        # Call download_item with the appropriate arguments
        self.download_thread = DownloadThread(self.category, self.name, self.quality)
        self.download_thread.progress.connect(self.window.update_progress)
        self.download_thread.start()

    # Update the UI progresbar
    def update_progress(self, value):
        self.window.progress_bar.setValue(value)

    # Import selected model and place it in viewport
    def import_model(self):
        path = getPath().get_inventory_path()

        # Construct the path to the .fbx file
        fbx_path = os.path.join(path, self.name, self.name + '_' + self.quality + '.fbx')

        # Import the .fbx file
        if os.path.exists(fbx_path):
            new_nodes = cmds.file(fbx_path, i=True, returnNewNodes=True)
            scale_factor = 2.0
            cmds.scale(scale_factor, scale_factor, scale_factor, new_nodes)
        else:
            print(f"File {fbx_path} does not exist.")

    # Create sky dome and set the HDRi light base map
    def create_HDRI_light(self):
        path = getPath().get_inventory_path()

        # Construct the path to the .hdri file
        hdri_path = os.path.join(path, self.name, self.name + '_' + self.quality + '.hdr')

        # Create an Arnold SkyDome light and set the .hdri file as its color
        if os.path.exists(hdri_path):
            skydome_light = cmds.shadingNode('aiSkyDomeLight', asLight=True)
            file_node = cmds.shadingNode('file', asTexture=True)
            cmds.setAttr(file_node + '.fileTextureName', hdri_path, type='string')
            cmds.setAttr(file_node + '.colorSpace', 'Raw', type='string')
            cmds.connectAttr(file_node + '.outColor', skydome_light + '.color')
        else:
            print(f"File {hdri_path} does not exist.")

    # Create and Assign maya phong shader to selected object
    def assign_texture(self):
        path = getPath().get_inventory_path()

        # Construct the path to the texture file
        name = self.name
        quality = self.quality
        print(name)
        print(quality)

        # get data from the JSON file
        with open(os.path.join(path, name, f"{name}.json")) as f:
            data = json.load(f)
        textures = data['blend'][quality]['blend']['include']
 
        # Initialize the texture paths
        diff_texture_path = None
        normal_texture_path = None
        roughness_texture_path = None
        displace_texture_path = None
        metal_texture_path = None

        # Find the texture paths based on the keywords in their names
        for texture_name, texture_info in textures.items():
            print(texture_name)
            if 'diff' in texture_name:
                diff_texture_path = os.path.join(path, name, texture_name)
            elif 'nor' in texture_name:
                normal_texture_path = os.path.join(path, name, texture_name)
            elif 'rough' in texture_name:
                roughness_texture_path = os.path.join(path, name, texture_name)
            elif 'disp' in texture_name:
                displace_texture_path = os.path.join(path, name, texture_name)
            elif 'metalic' in texture_name:
                metal_texture_path = os.path.join(path, name, texture_name)

        # Assign the new shader to the selected object
        selected_objects = cmds.ls(selection=True)

        # Create a Phong material and set the texture file as its color
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
        phong_shader = cmds.shadingNode('phong', asShader=True)
        
        # Connect the texture files to the corresponding attributes of the shader
        for texture_path, attribute in [(diff_texture_path, 'color'),
                                    (metal_texture_path, 'reflectivity')]:
            if (texture_path is not None):
                if os.path.exists(texture_path):
                    file_node = cmds.shadingNode('file', asTexture=True)
                    cmds.setAttr(file_node + '.fileTextureName', texture_path, type='string')
                    cmds.connectAttr(file_node + '.outColor', phong_shader + '.' + attribute)

        # Connect the normal map to a bump2d node and then to the normalCamera attribute
        if os.path.exists(normal_texture_path):
            file_node = cmds.shadingNode('file', asTexture=True)
            bump2d_node = cmds.shadingNode('bump2d', asUtility=True)
            cmds.setAttr(file_node + '.fileTextureName', normal_texture_path, type='string')
            cmds.connectAttr(file_node + '.outColorG', bump2d_node + '.bumpValue')
            cmds.setAttr(bump2d_node + '.bumpDepth', 0.2)
            cmds.connectAttr(bump2d_node + '.outNormal', phong_shader + '.normalCamera')

        # Connect the roughness texture
        if os.path.exists(roughness_texture_path):
            file_node = cmds.shadingNode('file', asTexture=True)
            set_range_node = cmds.shadingNode('setRange', asUtility=True)
            cmds.setAttr(file_node + '.fileTextureName', roughness_texture_path, type='string')
            cmds.connectAttr(file_node + '.outAlpha', set_range_node + '.valueX')
            cmds.connectAttr(set_range_node + '.outValueX', phong_shader + '.cosinePower')
            cmds.setAttr(set_range_node + '.minX', 2)
            cmds.setAttr(set_range_node + '.maxX', 100)
            cmds.setAttr(set_range_node + '.oldMinX', 0)
            cmds.setAttr(set_range_node + '.oldMaxX', 1)

        # Connect the displacement texture
        if os.path.exists(displace_texture_path):
            file_node = cmds.shadingNode('file', asTexture=True)
            set_disp_node = cmds.shadingNode('displacementShader', asUtility=True)
            cmds.setAttr(file_node + '.fileTextureName', displace_texture_path, type='string')
            cmds.setAttr(set_disp_node + '.scale', 0.05)
            cmds.connectAttr(file_node + '.outColor', set_disp_node + '.vectorDisplacement')
            cmds.connectAttr(set_disp_node + '.displacement', shading_group + '.displacementShader')

        cmds.setAttr(phong_shader + '.specularColor', 0.035, 0.035, 0.035, type='double3')
        cmds.setAttr(phong_shader + '.reflectivity', 0.035)
        cmds.connectAttr(phong_shader + '.outColor', shading_group + '.surfaceShader')

        if selected_objects:
            cmds.select(selected_objects)
            cmds.sets(selected_objects[0], edit=True, forceElement=shading_group)
        else:
            print("No object selected.")

    # Create and Assign Arnold aiSurface shader to selected object
    def assign_texture_arnold(self):
        path = getPath().get_inventory_path()
        name = self.name
        quality = self.quality

        # get data from the JSON file
        with open(os.path.join(path, name, f"{name}.json")) as f:
            data = json.load(f)
        textures = data['blend'][quality]['blend']['include']
 
        # Initialize the texture paths
        diff_texture_path = None
        normal_texture_path = None
        roughness_texture_path = None
        displace_texture_path = None
        metal_texture_path = None

        # Find the texture paths based on the keywords in their names
        for texture_name, texture_info in textures.items():
            print(texture_name)
            if 'diff' in texture_name:
                diff_texture_path = os.path.join(path, name, texture_name)
            elif 'nor' in texture_name:
                normal_texture_path = os.path.join(path, name, texture_name)
            elif 'rough' in texture_name:
                roughness_texture_path = os.path.join(path, name, texture_name)
            elif 'disp' in texture_name:
                displace_texture_path = os.path.join(path, name, texture_name)
            elif 'metalic' in texture_name:
                metal_texture_path = os.path.join(path, name, texture_name)

        # Assign the new shader to the selected object
        selected_objects = cmds.ls(selection=True)

        # Create an aiStandardSurface shader and set the texture file as its color
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
        arnold_shader  = cmds.shadingNode('aiStandardSurface', asShader=True)
        
        # Connect the texture files to the corresponding attributes of the shader
        for texture_path, attribute in [(diff_texture_path, 'baseColor'),
                                    (metal_texture_path, 'metalness')]:
            if (texture_path is not None):
                if os.path.exists(texture_path):
                    file_node = cmds.shadingNode('file', asTexture=True)
                    cmds.setAttr(file_node + '.fileTextureName', texture_path, type='string')
                    cmds.connectAttr(file_node + '.outColor', arnold_shader  + '.' + attribute)

        # Connect the normal map to a bump2d node and then to the normalCamera attribute
        if os.path.exists(normal_texture_path):
            file_node = cmds.shadingNode('file', asTexture=True)
            bump2d_node = cmds.shadingNode('bump2d', asUtility=True)
            cmds.setAttr(file_node + '.fileTextureName', normal_texture_path, type='string')
            cmds.connectAttr(file_node + '.outColorG', bump2d_node + '.bumpValue')
            cmds.setAttr(bump2d_node + '.bumpDepth', 0.005)
            cmds.connectAttr(bump2d_node + '.outNormal', arnold_shader  + '.normalCamera')

        # Connect the roughness texture
        if os.path.exists(roughness_texture_path):
            file_node = cmds.shadingNode('file', asTexture=True)
            set_range_node = cmds.shadingNode('setRange', asUtility=True)
            cmds.setAttr(file_node + '.fileTextureName', roughness_texture_path, type='string')
            cmds.connectAttr(file_node + '.outAlpha', set_range_node + '.valueX')
            cmds.connectAttr(set_range_node + '.outValueX', arnold_shader  + '.specularRoughness')
            cmds.setAttr(set_range_node + '.minX', 0.1)
            cmds.setAttr(set_range_node + '.maxX', 0.1)
            cmds.setAttr(set_range_node + '.oldMinX', 0)
            cmds.setAttr(set_range_node + '.oldMaxX', 1)

        # Connect the displacement texture
        if os.path.exists(displace_texture_path):
            file_node = cmds.shadingNode('file', asTexture=True)
            set_disp_node = cmds.shadingNode('displacementShader', asUtility=True)
            cmds.setAttr(file_node + '.fileTextureName', displace_texture_path, type='string')
            cmds.setAttr(set_disp_node + '.scale', 0.05)
            cmds.connectAttr(file_node + '.outColor', set_disp_node + '.vectorDisplacement')
            cmds.connectAttr(set_disp_node + '.displacement', shading_group + '.displacementShader')

        cmds.setAttr(arnold_shader  + '.specularColor', 1.0, 1.0, 1.0, type='double3')
        cmds.setAttr(arnold_shader  + '.specular', 0.25)
        cmds.connectAttr(arnold_shader  + '.outColor', shading_group + '.surfaceShader')

        if selected_objects:
            cmds.select(selected_objects)
            cmds.sets(selected_objects[0], edit=True, forceElement=shading_group)
        else:
            print("No object selected.")