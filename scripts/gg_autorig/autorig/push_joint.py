#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om

# Local imports
from gg_autorig.utils import data_export

# Dev only imports
from gg_autorig.utils.guides import guides_manager

reload(guides_manager)



def push_joint_make(parent=None, child=None, rotate="Y", translate="Z"):

    """
    Create a limb rig with controllers and constraints.
    This function sets up the basic structure for a limb, including controllers and constraints.
    """     

    data_exporter = data_export.DataExport()

    modules_grp = data_exporter.get_data("basic_structure", "modules_GRP")
    skel_grp = data_exporter.get_data("basic_structure", "skel_GRP")
    masterWalk_ctl = data_exporter.get_data("basic_structure", "masterWalk_CTL")

    side, module_name, suffix = child.split("_")

    individual_module_grp = cmds.createNode("transform", name=f"{side}_{module_name}PushModule_GRP", parent=modules_grp, ss=True)
    skinnging_grp = cmds.createNode("transform", name=f"{side}_{module_name}PushSkinningJoints_GRP", parent=skel_grp, ss=True)

    blend_matrix = cmds.createNode("blendMatrix", name=f"{side}_{module_name}Push_BLM", ss=True)
    parent_matrix = cmds.createNode("parentMatrix", name=f"{side}_{module_name}Push_PMX", ss=True)
    mult_double_linear = cmds.createNode("multDoubleLinear", name=f"{side}_{module_name}Push_MDL", ss=True)

    cmds.connectAttr(f"{parent}.worldMatrix[0]", f"{blend_matrix}.target[0].targetMatrix", force=True)
    cmds.connectAttr(f"{child}.worldMatrix[0]", f"{blend_matrix}.inputMatrix", force=True)

    cmds.setAttr(f"{blend_matrix}.target[0].translateWeight", 0)
    cmds.setAttr(f"{blend_matrix}.target[0].rotateWeight", 0.5)
    cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
    cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)

    cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{parent_matrix}.target[0].targetMatrix", force=True)
    cmds.connectAttr(f"{child}.worldMatrix[0]", f"{parent_matrix}.inputMatrix", force=True)

    temp_transform = cmds.createNode("transform", name=f"{side}_{module_name}Push_TempTransform", ss=True, parent=individual_module_grp)
    cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{temp_transform}.offsetParentMatrix", force=True)

    child_dag = om.MSelectionList().add(child).getDagPath(0)
    parent_dag = om.MSelectionList().add(temp_transform).getDagPath(0)

    child_world_matrix = child_dag.inclusiveMatrix()
    parent_world_matrix = parent_dag.inclusiveMatrix()
    
    offset_matrix = child_world_matrix * parent_world_matrix.inverse()

    cmds.setAttr(f"{parent_matrix}.target[0].offsetMatrix", offset_matrix, type="matrix")
    cmds.delete(temp_transform)


    cmds.select(clear=True)
    push_joint = cmds.joint(name=f"{side}_{module_name}Push_JNT")
    cmds.parent(push_joint, skinnging_grp)
    cmds.connectAttr(f"{parent_matrix}.outputMatrix", f"{push_joint}.offsetParentMatrix", force=True)
    cmds.addAttr(push_joint, ln="pushDistance", at="double", k=True, dv=1.0)
    cmds.addAttr(push_joint, ln="RotateValue", at="double", k=True, dv=0.5)
    cmds.addAttr(push_joint, ln="TranslateValue", at="double", k=True, dv=0)
    cmds.connectAttr(f"{push_joint}.pushDistance", f"{mult_double_linear}.input1", force=True)
    cmds.connectAttr(f"{child}.rotate{rotate}", f"{mult_double_linear}.input2", force=True)
    cmds.connectAttr(f"{mult_double_linear}.output", f"{push_joint}.translate{translate}", force=True)
    cmds.connectAttr(f"{push_joint}.RotateValue", f"{blend_matrix}.rotateWeight", force=True)
    cmds.connectAttr(f"{push_joint}.TranslateValue", f"{push_joint}.translateWeight", force=True)

push_joint_make(parent="L_shoulder_JNT", child="L_elbow_JNT")