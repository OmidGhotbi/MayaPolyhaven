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
            action1 = menu.addAction("Add Model to the scene")
            action2 = menu.addAction("Add Model and Convert Shader to Arnold")
            action1.triggered.connect(self.import_model)
            action2.triggered.connect(self.import_model_and_convert_arnold)
        action_download = menu.addAction("Download")
        
        action = menu.exec_(self.mapToGlobal(pos))
        if action == action_download:
            self.download_item()

    # Import model and convert its shader to Arnold
    def import_model_and_convert_arnold(self):
        path = getPath().get_inventory_path()
        fbx_path = os.path.join(path, self.name, self.name + '_' + self.quality + '.fbx')
        if os.path.exists(fbx_path):
            new_nodes = cmds.file(fbx_path, i=True, returnNewNodes=True)
            scale_factor = 2.0
            cmds.scale(scale_factor, scale_factor, scale_factor, new_nodes)
            cmds.select(new_nodes)
            self._auto_build_arnold_from_selection()
        else:
            print(f"File {fbx_path} does not exist.")

    # Arnold shader conversion logic (from provided script)
    def _auto_build_arnold_from_selection(self):
        import re
        MAP_KEYWORDS = {
            "baseColor": ["basecolor","base_color","albedo","diffuse","color","col","diff"],
            "roughness": ["rough","roughness","rgh","gloss","glossiness"],
            "metallic":  ["metallic","metalness","metal","mtl"],
            "normal":    ["normal","nrm","norm","normalgl","normal_opengl","normal_tangent","nor_gl"],
            "height":    ["height","disp","displacement"],
            "ao":        ["ao","occlusion","ambientocclusion"],
            "specular":  ["spec","specular","spc"],
            "opacity":   ["alpha","opacity","opac","transparency"],
        }
        EXTS = (".png",".jpg",".jpeg",".tif",".tiff",".exr",".tga",".bmp",".webp")

        def _get_shapes_from_selection():
            sels = cmds.ls(sl=True, long=True) or []
            shapes = []
            for s in sels:
                shapes += (cmds.listRelatives(s, shapes=True, fullPath=True) or [])
            for s in sels:
                if cmds.nodeType(s) in ("mesh","nurbsSurface","subdiv"):
                    shapes.append(s)
            return list(dict.fromkeys(shapes))

        def _get_materials(shape):
            mats = []
            sgs = cmds.listConnections(shape, type="shadingEngine") or []
            for sg in sgs:
                m = cmds.listConnections(sg + ".surfaceShader", s=True, d=False) or []
                mats += m
            return list(dict.fromkeys(mats))

        def _find_basecolor_file(shader):
            candidate_attrs = ["baseColor","color","diffuseColor","diffuse","base_color"]
            for attr in candidate_attrs:
                plug = "{}.{}".format(shader, attr)
                if not cmds.objExists(plug):
                    continue
                conns = cmds.listConnections(plug, s=True, d=False) or []
                for n in conns:
                    try:
                        if cmds.nodeType(n) == "file":
                            return n, cmds.getAttr(n + ".fileTextureName")
                        if cmds.nodeType(n) == "aiImage":
                            return n, cmds.getAttr(n + ".filename")
                    except:
                        pass
            return None, None

        def _classify_maps_in_folder(folder):
            result = {}
            if not folder or not os.path.isdir(folder):
                return result
            for f in os.listdir(folder):
                fl = f.lower()
                if not fl.endswith(EXTS):
                    continue
                for mtype, keys in MAP_KEYWORDS.items():
                    if any(k in fl for k in keys):
                        result.setdefault(mtype, []).append(os.path.join(folder, f).replace("\\","/"))
                        break
            return result

        def inspect_selected_materials():
            out = []
            for shp in _get_shapes_from_selection():
                for mat in _get_materials(shp):
                    node_type = cmds.nodeType(mat)
                    base_node, base_path = _find_basecolor_file(mat)
                    folder = os.path.dirname(base_path) if base_path else None
                    found = _classify_maps_in_folder(folder) if folder else {}
                    out.append({
                        "mesh": shp,
                        "material": mat,
                        "materialType": node_type,
                        "base_map_node": base_node,
                        "base_map_path": base_path,
                        "folder": folder,
                        "found_maps": found
                    })
            return out

        def _make_file_node(path, force_raw=False):
            fnode = cmds.shadingNode("file", asTexture=True, isColorManaged=True)
            p2d = cmds.shadingNode("place2dTexture", asUtility=True)
            for attr in ["coverage","translateFrame","rotateFrame","mirrorU","mirrorV","stagger","wrapU","wrapV",
                         "repeatUV","offset","rotateUV","noiseUV","vertexUvOne","vertexUvTwo","vertexUvThree","vertexCameraOne"]:
                if cmds.objExists(p2d + "." + attr) and cmds.objExists(fnode + "." + attr):
                    cmds.connectAttr(p2d + "." + attr, fnode + "." + attr, f=True)
            if cmds.objExists(p2d + ".outUV") and cmds.objExists(fnode + ".uvCoord"):
                cmds.connectAttr(p2d + ".outUV", fnode + ".uvCoord", f=True)
            if cmds.objExists(p2d + ".outUvFilterSize") and cmds.objExists(fnode + ".uvFilterSize"):
                cmds.connectAttr(p2d + ".outUvFilterSize", fnode + ".uvFilterSize", f=True)
            cmds.setAttr(fnode + ".fileTextureName", path, type="string")
            if force_raw:
                cmds.setAttr(fnode + ".colorSpace", "Raw", type="string")
            return fnode

        def build_ai_shader_from_maps(maps, basecolor_path, assign_to_mesh=None):
            shader_name = "AIShader_Auto"
            if basecolor_path:
                base_file = os.path.basename(basecolor_path)
                shader_name = re.sub(r'(_diff.*|_basecolor.*|_albedo.*)', '', os.path.splitext(base_file)[0])
            shader = cmds.shadingNode("aiStandardSurface", asShader=True, name=shader_name)
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader + "SG")
            cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", f=True)
            if "baseColor" in maps:
                f = _make_file_node(maps["baseColor"][0])
                cmds.connectAttr(f + ".outColor", shader + ".baseColor", f=True)
            if "roughness" in maps:
                f = _make_file_node(maps["roughness"][0], force_raw=True)
                cmds.connectAttr(f + ".outAlpha", shader + ".specularRoughness", f=True)
            if "metallic" in maps:
                f = _make_file_node(maps["metallic"][0], force_raw=True)
                cmds.connectAttr(f + ".outAlpha", shader + ".metalness", f=True)
            if "opacity" in maps:
                f = _make_file_node(maps["opacity"][0], force_raw=True)
                cmds.connectAttr(f + ".outColor", shader + ".opacity", f=True)
            if "normal" in maps:
                f = _make_file_node(maps["normal"][0], force_raw=True)
                bump = cmds.shadingNode("aiNormalMap", asShader=True, name=shader_name + "_NormalMap")
                cmds.connectAttr(f + ".outColor", bump + ".input", f=True)
                cmds.connectAttr(bump + ".outValue", shader + ".normalCamera", f=True)
            if assign_to_mesh:
                cmds.sets(assign_to_mesh, e=True, forceElement=sg)
            return shader

        infos = inspect_selected_materials()
        if not infos:
            cmds.warning(" No valid materials/maps found on selection.")
            return
        for d in infos:
            if not d["found_maps"]:
                cmds.warning("No maps detected in folder for: " + d["mesh"])
                continue
            print(" Building shader for", d["mesh"], "from folder:", d["folder"])
            build_ai_shader_from_maps(d["found_maps"], d["base_map_path"], assign_to_mesh=d["mesh"])
    
    
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