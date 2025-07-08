import maya.cmds as cmds
import maya.OpenMaya as om
import os
import json
from gg_autorig.utils import core
from importlib import reload
reload(core)





def guides_export(file_name=None):
        """
        Exports the guides from the selected folder in the Maya scene to a JSON file.
        """

        TEMPLATE_FILE = core.init_template_file(ext=".guides")
        
        guides_folder = cmds.ls(sl=True) or cmds.ls("guides_GRP", type="transform")

        if guides_folder:
                guides_descendents = [
                                node for node in cmds.listRelatives(guides_folder[0], allDescendents=True, type="transform")
                                if "buffer" not in node.lower() and "_guide_crv" not in node.lower()
                ]


                if not guides_descendents:
                        om.MGlobal.displayError("No guides found in the scene.")
                        return

                guides_get_rotation = [cmds.xform(guide, q=True, ws=True, rotation=True) for guide in guides_descendents]
                guides_get_translation = [cmds.xform(guide, q=True, ws=True, translation=True) for guide in guides_descendents]
                guides_parents = [cmds.listRelatives(guide, parent=True)[0] for guide in guides_descendents]



        else:
                om.MGlobal.displayError("No guides found in the scene.")
                return
        
        guides_name = os.path.splitext(os.path.basename(TEMPLATE_FILE))[0]

        guides_data = {guides_name: {}}

        for i, guide in enumerate(guides_descendents):
                guides_data[guides_name][guide] = {
                        "worldPosition": guides_get_translation[i],
                        "worldRotation": guides_get_rotation[i],
                        "parent": guides_parents[i],
                }


        with open(os.path.join(TEMPLATE_FILE), "w") as outfile:
                json.dump(guides_data, outfile, indent=4)

        om.MGlobal.displayInfo(f"Guides data exported to {TEMPLATE_FILE}")

def guide_import(joint_name, all_descendents=True, path=None):
        """
        Imports guides from a JSON file into the Maya scene.
        
        Args:
                joint_name (str): The name of the joint to import. If "all", imports all guides.
                all_descendents (bool): If True, imports all descendents of the specified joint. Defaults to True.
        Returns:
                list: A list of imported joint names if joint_name is not "all", otherwise returns the world position and rotation of the specified joint.
        """

        TEMPLATE_FILE = core.init_template_file(ext=".guides", export=False, path=path)


        name = os.path.splitext(os.path.basename(TEMPLATE_FILE))[0]


        with open(TEMPLATE_FILE, "r") as infile:
                guides_data = json.load(infile)
        
        joints_chain = []                    


        # for main_joint_name, data in guides_data[name].items():
        #                 if main_joint_name == joint_name:
        #                                 cmds.select(clear=True) 
        #                                 if "isLocator" in data and data["isLocator"]:
        #                                         return data["worldPosition"], data["worldRotation"]
        #                                 else:
        #                                         main_joint = cmds.joint(name=main_joint_name, rad=50)
        #                                 cmds.setAttr(f"{main_joint}.translate", data["worldPosition"][0], data["worldPosition"][1], data["worldPosition"][2])
        #                                 cmds.setAttr(f"{main_joint}.rotate", data["worldRotation"][0], data["worldRotation"][1], data["worldRotation"][2])
        #                                 cmds.makeIdentity(main_joint, apply=True, r=True)
        #                                 cmds.setAttr(f"{main_joint}.preferredAngle", data["preferredAngle"][0], data["preferredAngle"][1], data["preferredAngle"][2])
        #                                 joints_chain.append(main_joint_name)
        #                                 break

        # if all_descendents:
        #         parent_map = {joint: data.get("parent") for joint, data in guides_data[name].items()}                             
        #         processing_queue = [joint for joint, parent in parent_map.items() if parent == joint_name]      
                
        #         while processing_queue:
        #                         joint = processing_queue.pop(0)
        #                         cmds.select(clear=True)
        #                         imported_joint = cmds.joint(name=joint, rad=50)
        #                         cmds.setAttr(f"{imported_joint}.translate", guides_data[name][joint]["worldPosition"][0], guides_data[name][joint]["worldPosition"][1], guides_data[name][joint]["worldPosition"][2])
        #                         cmds.setAttr(f"{imported_joint}.rotate", guides_data[name][joint]["worldRotation"][0], guides_data[name][joint]["worldRotation"][1], guides_data[name][joint]["worldRotation"][2])
        #                         cmds.makeIdentity(imported_joint, apply=True, r=True)
        #                         cmds.setAttr(f"{imported_joint}.preferredAngle", guides_data[name][joint]["preferredAngle"][0], guides_data[name][joint]["preferredAngle"][1], guides_data[name][joint]["preferredAngle"][2])  
        #                         parent = parent_map[joint]
        #                         if parent != "C_root_JNT":
        #                                 cmds.parent(imported_joint, parent)
        #                         joints_chain.append(joint)
        #                         processing_queue.extend([child for child, parent in parent_map.items() if parent == joint])
                
        # cmds.select(clear=True)
        # if joints_chain:
        #         return joints_chain
        

def fk_chain_import():
        """
        Finds all guide names containing 'FK' that either have no parent or their parent is 'C_guides_GRP'.
        Returns:
                list: List of FK guide names matching the criteria.
        """
        if not TEMPLATE_FILE:
                complete_path = os.path.realpath(__file__)
                relative_path = complete_path.split("\scripts")[0]
                guides_path = os.path.join(relative_path, "guides")
                # Find the first .guides file in the directory
                guide_files = [f for f in os.listdir(guides_path) if f.endswith('.guides')]
                if not guide_files:
                        om.MGlobal.displayError("No .guides files found in guides directory.")
                        return []
                file_path = os.path.join(guides_path, guide_files[0])
        else:
                file_path = os.path.normpath(TEMPLATE_FILE)

        with open(file_path, "r") as infile:
                guides_data = json.load(infile)

        # Get the main key (guide set name)
        guide_set_name = next(iter(guides_data))
        fk_guides = []
        for guide_name, data in guides_data[guide_set_name].items():
                if "FK" in guide_name:
                        parent = data.get("parent")
                        if not parent or parent == "C_guides_GRP":
                                fk_guides.append(guide_name)
        return fk_guides
                
