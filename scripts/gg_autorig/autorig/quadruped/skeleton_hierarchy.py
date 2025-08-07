#Python libraries import
from maya import cmds
from importlib import reload

# Tools / utils import
from gg_autorig.utils import data_export


def parented_chain(skinning_joints, parent):

    data_exporter = data_export.DataExport()

    skelHierarchy_grp = data_exporter.get_data("basic_structure", "skeletonHierarchy_GRP")

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


def get_data():
    """
    Retrieve the basic structure data for the rig, including guides and modules.
    Returns:
        dict: A dictionary containing the basic structure data.
    """

    data_exporter = data_export.DataExport()

    spine_transform = data_exporter.get_data("C_spineModule", "skinning_transform")
    neck_transform = data_exporter.get_data("C_neckModule", "skinning_transform")
    trunk_transform = data_exporter.get_data("C_trunkModule", "skinning_transform")



    spine_list = cmds.listRelatives(spine_transform, children=True, type="joint")

    spine_chain = parented_chain(spine_list, parent=None)

    neck_list = cmds.listRelatives(neck_transform, children=True, type="joint")

    neck_chain = parented_chain(neck_list, parent=spine_chain[-2])

    trunk_list = cmds.listRelatives(trunk_transform, children=True, type="joint")

    trunk_chain = parented_chain(trunk_list, parent=neck_chain[-1])

    modules = [
        ("L_frontLegModule", "skinning_transform", spine_chain[-2]),
        ("R_frontLegModule", "skinning_transform", spine_chain[-2]),
        ("L_backLegModule", "skinning_transform", spine_chain[-1]),
        ("R_backLegModule", "skinning_transform", spine_chain[-1]),
    ]

    for module_name, attr, parent_joint in modules:
        module_transform = data_exporter.get_data(module_name, attr)
        joint_list = cmds.listRelatives(module_transform, children=True, type="joint")
        parented_chain(joint_list, parent_joint)
