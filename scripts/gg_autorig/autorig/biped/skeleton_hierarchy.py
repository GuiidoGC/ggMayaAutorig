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

    l_arm = data_exporter.get_data("L_armModule", "skinning_transform")
    r_arm = data_exporter.get_data("R_armModule", "skinning_transform")

    l_leg = data_exporter.get_data("L_legModule", "skinning_transform")
    r_leg = data_exporter.get_data("R_legModule", "skinning_transform")

    spine_list = cmds.listRelatives(spine_transform, children=True, type="joint")

    spine_chain = parented_chain(spine_list, parent=None)

    neck_list = cmds.listRelatives(neck_transform, children=True, type="joint")

    neck_chain = parented_chain(neck_list, parent=spine_chain[-2])

    for arm, leg in zip([l_arm, r_arm], [l_leg, r_leg]):

        arm_list = cmds.listRelatives(arm, children=True, type="joint")
        leg_list = cmds.listRelatives(leg, children=True, type="joint")


        arm = parented_chain(arm_list, spine_chain[-2])
        leg = parented_chain(leg_list, spine_chain[-1])
