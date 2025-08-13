#Python libraries import
from maya import cmds
from importlib import reload
import os
import json
import maya.api.OpenMaya as om

# Tools / utils import
from gg_autorig.utils import data_export
from gg_autorig.utils import core

reload(core)



def parented_chain(skinning_joints, parent):

    data_exporter = data_export.DataExport()

    skelHierarchy_grp = data_exporter.get_data("basic_structure", "skeletonHierarchy_GRP")

    try:
        env_replace = parent.replace("_JNT", "_ENV")
        if cmds.objExists(env_replace):
            parent = env_replace
    except Exception as e:
        parent = parent

    joints = []

    for joint in skinning_joints:
        cmds.select(clear=True)
        joint_env = cmds.createNode("joint", n=joint.replace("_JNT", "_ENV"))
        cube = cmds.polyCube(name=f"{joint_env}_Shape", w=1, h=1, d=1)
        cmds.parent(cube[0], joint_env)

        if "localHip" in joint_env:
            cmds.parent(joint_env, joints[0])
            joints.append(joint_env)

            continue

        if joints:

            cmds.parent(joint_env, joints[-1])

        elif parent:
            cmds.parent(joint_env, parent)

        elif parent is None:
            cmds.parent(joint_env, skelHierarchy_grp)
        
        joints.append(joint_env)

    for i, joint in enumerate(joints):
        
        if parent is None:

            cmds.connectAttr(skinning_joints[i] + ".worldMatrix[0]", joint + ".offsetParentMatrix", force=True)
        
        elif parent:
            mult_matrix = cmds.createNode("multMatrix", n=joint.replace("_ENV", "_MMX"), ss=True)
            cmds.connectAttr(skinning_joints[i] + ".worldMatrix[0]", mult_matrix + ".matrixIn[0]", force=True)
            cmds.connectAttr(parent + ".worldInverseMatrix[0]", mult_matrix + ".matrixIn[1]", force=True)
            cmds.connectAttr(mult_matrix + ".matrixSum", joint + ".offsetParentMatrix", force=True)

            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                cmds.setAttr(joint + "." + attr, 0)
            
        

        if "localHip" in joint:
            mult_matrix = cmds.createNode("multMatrix", n=joint.replace("_ENV", "_MMX"), ss=True)
            cmds.connectAttr(skinning_joints[i] + ".worldMatrix[0]", mult_matrix + ".matrixIn[0]", force=True)
            cmds.connectAttr(joints[0] + ".worldInverseMatrix[0]", mult_matrix + ".matrixIn[1]", force=True)
            cmds.connectAttr(mult_matrix + ".matrixSum", joint + ".offsetParentMatrix", force=True)

            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                cmds.setAttr(joint + "." + attr, 0)

        elif i != 0:
            mult_matrix = cmds.createNode("multMatrix", n=joint.replace("_ENV", "_MMX"), ss=True)
            cmds.connectAttr(skinning_joints[i] + ".worldMatrix[0]", mult_matrix + ".matrixIn[0]", force=True)
            cmds.connectAttr(joints[i-1] + ".worldInverseMatrix[0]", mult_matrix + ".matrixIn[1]", force=True)
            cmds.connectAttr(mult_matrix + ".matrixSum", joint + ".offsetParentMatrix", force=True)

            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                cmds.setAttr(joint + "." + attr, 0)

            
        

        
    return joints


def build_complete_hierarchy():
    """
    Reads the build and guide files, interprets the desired hierarchy, and
    constructs it in Maya by parenting the corresponding skinning groups.
    Uses file locations relative to the current script.
    """
    try:
        complete_path = os.path.realpath(__file__)
        relative_path = complete_path.split("scripts")[0]
        build_path = os.path.join(relative_path, "build", "build_cache.cache")
        
        with open(build_path, "r") as f:
            build_data = json.load(f)

        guides_path = core.init_template_file(ext=".guides", export=False)
        
        with open(guides_path, "r") as f:
            guides_data = json.load(f)

    except IOError as e:
        om.MGlobal.displayError(f"File error: Could not find or read a data file. {e}")
        return
    except json.JSONDecodeError as e:
        om.MGlobal.displayError(f"JSON error: The file is malformed. {e}")
        return
    except Exception as e:
        om.MGlobal.displayError(f"Unexpected error while loading files: {e}")
        return

    skel_grps = []
    skinning_joints = []
    for module, data in build_data.items():
        for value in data.items():
            if "skinning_transform" in value:
                    joints = cmds.listRelatives(value[1], allDescendents=True, type="joint")
                    skel_grps.append((value[1]))
                    skinning_joints.append(joints)

    skel_grps_to_modules = []
    for group in skel_grps:
        module_side  = group.split("_")[0]
        
        try:
            enum_text = cmds.attributeQuery('moduleName', node=group, listEnum=True)[0].split(':')[0]
            skel_grps_to_modules.append((module_side, enum_text))
        except Exception as e:
            om.MGlobal.displayError(f"Error getting attribute for {group}: {e}")

    parent_child_pairs = []
    hierarchy_list = guides_data.get("hierarchy", [])
    stack = [(None, item) for item in hierarchy_list]

    while stack:
        parent_name, current_item = stack.pop()
        for key, children in current_item.items():
            if parent_name:
                parent_child_pairs.append((parent_name, key))
            for child in children:
                if isinstance(child, dict):
                    stack.append((key, child))

    for parent, child in parent_child_pairs:
        parent_side, parent_module = parent.split("_")[0], parent.split("_")[1]
        child_side, child_module = child.split("_")[0], child.split("_")[1]
        if child_module == "localHip" and parent_module == "spine":
            continue

        for i, (side, grp) in enumerate(skel_grps_to_modules):
            match_parent_module = "spine" if parent_module == "localHip" else parent_module
            match_child_module = "spine" if child_module == "localHip" else child_module

            if side == parent_side and grp == match_parent_module:
                parent_index = i

            elif side == child_side and grp == match_child_module:
                child_index = i
            elif match_parent_module == "root":
                parent_index = "Skip"
                continue

        parent_index_chain = -1 if not parent_module == "spine" else -2


        if parent_module == "root":
            parented_chain(skinning_joints=skinning_joints[child_index], parent=None)
        else:
            parented_chain(skinning_joints=skinning_joints[child_index], parent=skinning_joints[parent_index][parent_index_chain])




