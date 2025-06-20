import maya.cmds as cmds
import maya.OpenMaya as om
import os
import json


TEMPLATE_FILE = None

def init_template_file(path=None):
    """
    Initializes the TEMPLATE_FILE variable.
    If a path is provided, it sets TEMPLATE_FILE to that path.
    Otherwise, it uses the default template file path.
    """
    global TEMPLATE_FILE
    if path:
        TEMPLATE_FILE = path
    else:
        complete_path = os.path.realpath(__file__)
        relative_path = complete_path.split("\scripts")[0]
        TEMPLATE_FILE = os.path.join(relative_path, "guides", "dragon_guides_template_01.guides")


def guides_export():
        """
        Exports the guides from the selected folder in the Maya scene to a JSON file.
        """
        
        guides_folder = cmds.ls(sl=True)
        answer = cmds.promptDialog(
                title="INPUT DIALOG",
                message="INSERT FILE NAME",
                button=["OK", "Cancel"],
                defaultButton="OK",
                cancelButton="Cancel",
                dismissString="Cancel")
        if answer == "Cancel":
                return
        guides_name = cmds.promptDialog(query=True, text=True)

        if guides_folder:
                guides_descendents = cmds.listRelatives(guides_folder[0], allDescendents=True, type="joint")
                if not guides_descendents:
                        om.MGlobal.displayError("No guides found in the scene.")
                        return

                left_guides = []
                right_guides = []
                for guide in guides_descendents:
                        if guide.split("_")[0] == "L":
                                left_guides.append(guide)
                        if guide.split("_")[0] == "R":
                                right_guides.append(guide)
                for left_guide in left_guides:
                        splited_guide = left_guide.split("_")[1]
                        for right_guide in right_guides:
                                if splited_guide in right_guide:
                                        left_world_position = [round(coord, 3) for coord in cmds.xform(left_guide, q=True, ws=True, t=True)]
                                        right_world_position = [round(coord, 3) for coord in cmds.xform(right_guide, q=True, ws=True, t=True)]

                                        right_world_position[0] = right_world_position[0] * -1                                               

                
                if len(left_guides) != len(right_guides):
                        om.MGlobal.displayWarning("Guides are not symmetrical.")
                        return
                
                guides_get_rotation = [cmds.xform(guide, q=True, ws=True, rotation=True) for guide in guides_descendents]
                guides_get_translation = [cmds.xform(guide, q=True, ws=True, translation=True) for guide in guides_descendents]
                guides_parents = [cmds.listRelatives(guide, parent=True)[0] for guide in guides_descendents]
                guides_prefered_angle = [cmds.getAttr(f"{guide}.preferredAngle")[0] for guide in guides_descendents]

                guides_loc_descendants = cmds.listRelatives(guides_folder[0], allDescendents=True, type="locator")
                guides_loc_get_rotation = [cmds.xform(guide.replace("Shape", ""), q=True, ws=True, rotation=True) for guide in guides_loc_descendants]
                guides_loc_get_translation = [cmds.xform(guide.replace("Shape", ""), q=True, ws=True, translation=True) for guide in guides_loc_descendants]


        else:
                om.MGlobal.displayError("No guides found in the scene.")
                return

        complete_path = os.path.realpath(__file__)
        relative_path = complete_path.split("\scripts")[0]
        final_path = os.path.join(relative_path, "guides")
        guides_data = {guides_name: {}}

        for i, guide in enumerate(guides_descendents):
                guides_data[guides_name][guide] = {
                        "worldPosition": guides_get_translation[i],
                        "worldRotation": guides_get_rotation[i],
                        "preferredAngle": guides_prefered_angle[i],     
                        "parent": guides_parents[i],
                }

        if guides_loc_descendants:
                for i, guide in enumerate(guides_loc_descendants):
                        guides_data[guides_name][guide.replace("Shape", "")] = {
                                "worldPosition": guides_loc_get_translation[i],
                                "worldRotation": guides_loc_get_rotation[i],
                                "isLocator": True,
                        }

        if not os.path.exists(final_path):
                os.makedirs(final_path)

        with open(os.path.join(final_path, f'{guides_name}.guides'), "w") as outfile:
                json.dump(guides_data, outfile, indent=4)

        om.MGlobal.displayInfo(f"Guides data exported to {os.path.join(final_path, f'{guides_name}.json')}")


def guide_import(joint_name, all_descendents=True):
        """
        Imports guides from a JSON file into the Maya scene.
        
        Args:
                joint_name (str): The name of the joint to import. If "all", imports all guides.
                all_descendents (bool): If True, imports all descendents of the specified joint. Defaults to True.
        Returns:
                list: A list of imported joint names if joint_name is not "all", otherwise returns the world position and rotation of the specified joint.
        """

        filePath = TEMPLATE_FILE

        if not filePath:
                complete_path = os.path.realpath(__file__)
                relative_path = complete_path.split("\scripts")[0]
                guides_path = os.path.join(relative_path, "guides")

                final_path = cmds.fileDialog2(fileMode=1, caption="Select JSON file", dir=guides_path, okCaption="Select")[0]

                if not final_path:
                        om.MGlobal.displayError("No file selected.")
                        return
        else:
                final_path = os.path.normpath(filePath)

        name = os.path.basename(final_path).split(".")[0]

        with open(final_path, "r") as infile:
                guides_data = json.load(infile)
        
        joints_chain = []
        if joint_name == "all":
                if not cmds.ls("C_guides_GRP"):
                        guides_node = cmds.createNode("transform", name="C_guides_GRP")
                else:
                        guides_node = "C_guides_GRP"
                for joint, data in reversed(list(guides_data[name].items())):
                        cmds.select(clear=True)
                        if "isLocator" in data and data["isLocator"]:
                               loc = cmds.spaceLocator(name=joint)[0]
                               cmds.xform(loc, ws=True, t=(data["worldPosition"][0], data["worldPosition"][1], data["worldPosition"][2]))
                               cmds.xform(loc, ws=True, ro=(data["worldRotation"][0], data["worldRotation"][1], data["worldRotation"][2]))
                               cmds.parent(loc, guides_node)
                               cmds.setAttr(f"{loc}.localScaleX", 100)
                               cmds.setAttr(f"{loc}.localScaleY", 100)
                               cmds.setAttr(f"{loc}.localScaleZ", 100)
                               
                        else:
                                imported_joint = cmds.joint(name=joint, rad=50)

                                cmds.setAttr(f"{imported_joint}.translate", data["worldPosition"][0], data["worldPosition"][1], data["worldPosition"][2])
                                cmds.setAttr(f"{imported_joint}.rotate", data["worldRotation"][0], data["worldRotation"][1], data["worldRotation"][2])
                                cmds.makeIdentity(imported_joint, apply=True, r=True)
                                cmds.setAttr(f"{imported_joint}.preferredAngle", data["preferredAngle"][0], data["preferredAngle"][1], data["preferredAngle"][2])
                                if data.get("parent"):
                                        if data["parent"] == "C_root_JNT":
                                                cmds.parent(imported_joint, guides_node)   
                                        else:
                                                cmds.parent(joint, data["parent"])                        

        else:
                for main_joint_name, data in guides_data[name].items():
                                if main_joint_name == joint_name:
                                                cmds.select(clear=True) 
                                                if "isLocator" in data and data["isLocator"]:
                                                        return data["worldPosition"], data["worldRotation"]
                                                else:
                                                        main_joint = cmds.joint(name=main_joint_name, rad=50)
                                                cmds.setAttr(f"{main_joint}.translate", data["worldPosition"][0], data["worldPosition"][1], data["worldPosition"][2])
                                                cmds.setAttr(f"{main_joint}.rotate", data["worldRotation"][0], data["worldRotation"][1], data["worldRotation"][2])
                                                cmds.makeIdentity(main_joint, apply=True, r=True)
                                                cmds.setAttr(f"{main_joint}.preferredAngle", data["preferredAngle"][0], data["preferredAngle"][1], data["preferredAngle"][2])
                                                joints_chain.append(main_joint_name)
                                                break

                if all_descendents:
                        parent_map = {joint: data.get("parent") for joint, data in guides_data[name].items()}                             
                        processing_queue = [joint for joint, parent in parent_map.items() if parent == joint_name]      
                        
                        while processing_queue:
                                        joint = processing_queue.pop(0)
                                        cmds.select(clear=True)
                                        imported_joint = cmds.joint(name=joint, rad=50)
                                        cmds.setAttr(f"{imported_joint}.translate", guides_data[name][joint]["worldPosition"][0], guides_data[name][joint]["worldPosition"][1], guides_data[name][joint]["worldPosition"][2])
                                        cmds.setAttr(f"{imported_joint}.rotate", guides_data[name][joint]["worldRotation"][0], guides_data[name][joint]["worldRotation"][1], guides_data[name][joint]["worldRotation"][2])
                                        cmds.makeIdentity(imported_joint, apply=True, r=True)
                                        cmds.setAttr(f"{imported_joint}.preferredAngle", guides_data[name][joint]["preferredAngle"][0], guides_data[name][joint]["preferredAngle"][1], guides_data[name][joint]["preferredAngle"][2])  
                                        parent = parent_map[joint]
                                        if parent != "C_root_JNT":
                                                cmds.parent(imported_joint, parent)
                                        joints_chain.append(joint)
                                        processing_queue.extend([child for child, parent in parent_map.items() if parent == joint])
                
        cmds.select(clear=True)
        if joints_chain:
                return joints_chain
        

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
                
