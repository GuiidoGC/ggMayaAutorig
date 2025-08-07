import maya.cmds as cmds
import maya.api.OpenMaya as om
from gg_autorig.utils import data_export


def get_offset_matrix(child, parent):
    """
    Calculate the offset matrix between a child and parent transform in Maya.
    Args:
        child (str): The name of the child transform.
        parent (str): The name of the parent transform. 
    Returns:
        om.MMatrix: The offset matrix that transforms the child into the parent's space.
    """
    child_dag = om.MSelectionList().add(child).getDagPath(0)
    parent_dag = om.MSelectionList().add(parent).getDagPath(0)
    
    child_world_matrix = child_dag.inclusiveMatrix()
    parent_world_matrix = parent_dag.inclusiveMatrix()
    
    offset_matrix = child_world_matrix * parent_world_matrix.inverse()

    
    return offset_matrix

def switch_matrix_space(target, sources = [None], default_value=1): 
    """
    Switch the matrix space of a target control to multiple source controls in Maya.

    Args:
        target (str): The name of the target control to switch space for.
        sources (list, optional): A list of source controls to switch to. Defaults to [None].
        default_value (float, optional): The default value for the follow attribute. Defaults to 1.
    """

    target_grp = target.replace("CTL", "GRP")
    if not cmds.objExists(target):
        target_grp = target
    if not cmds.objExists(target_grp):
        om.MGlobal.displayError(f"Target group '{target_grp}' does not exist.")
        return
    
    
    parent_matrix = cmds.createNode("parentMatrix", name=target.replace("CTL", "PM"), ss=True)
    mult_matrix = cmds.createNode("multMatrix", name=target.replace("_CTL", "OffsetParent_MMX"), ss=True)   
    cmds.connectAttr(f"{target_grp}.worldMatrix[0]", f"{parent_matrix}.inputMatrix")
    cmds.connectAttr(f"{parent_matrix}.outputMatrix", f"{mult_matrix}.matrixIn[0]")
    cmds.connectAttr(f"{target_grp}.worldInverseMatrix[0]", f"{mult_matrix}.matrixIn[1]")
    target_matrix = cmds.getAttr(f"{target_grp}.worldInverseMatrix[0]")

    condition_nodes = []
    spaces = []
    
    for i, matrix in enumerate(sources):

        matrix_offset = get_offset_matrix(target_grp, matrix)

        cmds.connectAttr(f"{matrix}.worldMatrix[0]", f"{parent_matrix}.target[{i}].targetMatrix")
        cmds.setAttr(f"{parent_matrix}.target[{i}].offsetMatrix", matrix_offset, type="matrix")

        name = matrix.split("_")[1]
        name = name[0].upper() + name[1:].lower()

        replace_name = f"{name}_COND"

        condition = cmds.createNode("condition", name=f"{target.replace('_CTL', replace_name)}", ss=True)
        cmds.setAttr(f"{condition}.firstTerm", i)
        cmds.setAttr(f"{condition}.operation", 0)
        cmds.setAttr(f"{condition}.colorIfFalseR", 0)

        condition_nodes.append(condition)
        spaces.append(name)

    cmds.addAttr(target, longName="SpaceSwitchSep", niceName = "SpaceSwitches_____", attributeType="enum", enumName="____", keyable=True)
    cmds.setAttr(f"{target}.SpaceSwitchSep", channelBox=True, lock=True)   
    if len(sources) == 1:     
        cmds.addAttr(target, longName="SpaceSwitch", attributeType="enum", enumName=":".join(spaces), keyable=False)
        cmds.setAttr(f"{target}.SpaceSwitchSep", channelBox=True, lock=True)   
    else:
        cmds.addAttr(target, longName="SpaceSwitch", attributeType="enum", enumName=":".join(spaces), keyable=True)

    cmds.addAttr(target, longName="FollowValue", attributeType="float", min=0, max=1, defaultValue=default_value, keyable=True)

    for i, condition in enumerate(condition_nodes):
        cmds.connectAttr(f"{target}.SpaceSwitch", f"{condition}.secondTerm")
        cmds.connectAttr(f"{target}.FollowValue", f"{condition}.colorIfTrueR")
        cmds.connectAttr(f"{condition}.outColorR", f"{parent_matrix}.target[{i}].weight")

    
    cmds.connectAttr(f"{mult_matrix}.matrixSum", f"{target}.offsetParentMatrix")




def leg_pv_spaceswitch(localHip, legPv, footCtl, root):

    side = legPv.split("_")[0]
    pv_SPC = legPv.replace("_CTL", "_SDK")
  
    cmds.addAttr(legPv, shortName="spaceSwitchSep", niceName="SPACE SWITCH_____", enumName="_____",attributeType="enum", keyable=True)
    cmds.setAttr(legPv+".spaceSwitchSep", channelBox=True, lock=True)
    cmds.addAttr(legPv, shortName="automaticPoleVector", niceName="Automatic PoleVector", maxValue=1, minValue=0,defaultValue=1, keyable=True)
    cmds.addAttr(legPv, shortName="spaceSwitchValue", niceName="Space Switch Value", maxValue=1, minValue=0,defaultValue=1, keyable=True)

    pelvis_trn = cmds.createNode("transform", name=f"{side}_followPelvis_TRN", parent=f"{side}_legModule_GRP")
    foot_trn = cmds.createNode("transform", name=f"{side}_followFoot_TRN", parent=pelvis_trn)

    cmds.pointConstraint(root, pelvis_trn, maintainOffset=False)  

    cmds.aimConstraint(
        footCtl, pelvis_trn, 
        aimVector=(0, -1, 0), 
        upVector=(1, 0, 0), 
        worldUpType="objectrotation", 
        worldUpVector=(1, 0, 0), 
        worldUpObject=localHip
    )

    cmds.aimConstraint(
        footCtl, foot_trn,
        aimVector=(0, -1, 0),
        upVector=(1, 0, 0),
        worldUpType="objectrotation",
        worldUpVector=(1, 0, 0),
        worldUpObject=footCtl,
        maintainOffset=False
    )

    cmds.parentConstraint(foot_trn, pv_SPC, maintainOffset=True)

    cmds.setKeyframe(foot_trn, attribute="rotate")
    cmds.setKeyframe(pv_SPC, attribute="rotate")
    cmds.setKeyframe(pv_SPC, attribute="translate")

    cmds.connectAttr(f"{legPv}.spaceSwitchValue", f"{foot_trn}.blendAim1")
    cmds.connectAttr(f"{legPv}.automaticPoleVector", f"{pv_SPC}.blendParent1")

def fk_switch(target, sources = [], default_rotate = 1, default_translate = 1):
    """
    Switch the matrix space of a target control to multiple source controls in Maya.

    Args:
        target (str): The name of the target control to switch space for.
        sources (list, optional): A list of source controls to switch to. Defaults to [None].
        default_value (float, optional): The default value for the follow attribute. Defaults to 1.
    """

    target_grp = target.replace("CTL", "GRP")
    if not cmds.objExists(target):
        target_grp = target
    if not cmds.objExists(target_grp):
        om.MGlobal.displayError(f"Target group '{target_grp}' does not exist.")
        return
    
    cmds.setAttr(f"{target_grp}.inheritsTransform", 0)


    connections = cmds.listConnections(f"{target_grp}.offsetParentMatrix", plugs=True, source=True, destination=False)[0]

    data_exporter = data_export.DataExport()


    masterWalk_ctl = data_exporter.get_data("basic_structure", "masterWalk_CTL")


    parent_matrix_masterwalk = cmds.createNode("parentMatrix", name=target.replace("_CTL", "MasterwalkSpace_PM"), ss=True)
    parent_matrix_parents = cmds.createNode("parentMatrix", name=target.replace("_CTL", "Space_PM"), ss=True)
    blend_matrix = cmds.createNode("blendMatrix", name=target.replace("_CTL", "Space_BMX"), ss=True)

    cmds.addAttr(target, longName="SpaceSwitchSep", niceName = "Space Switches  ———", attributeType="enum", enumName="———", keyable=True)
    cmds.setAttr(f"{target}.SpaceSwitchSep", channelBox=True, lock=True)   

    spaces = [src.split("_")[1] for src in sources]


    if len(sources) > 1:
        cmds.addAttr(target, longName="SpaceFollow", attributeType="enum", enumName=":".join(spaces), keyable=True)

        for i, driver in enumerate(sources):

            condition = cmds.createNode("condition", name=target.replace('_CTL', f"Space0{i}_CON"), ss=True)
            cmds.setAttr(f"{condition}.firstTerm", i)
            cmds.connectAttr(f"{target}.SpaceFollow", f"{condition}.secondTerm")
            cmds.setAttr(f"{condition}.operation", 0)
            cmds.setAttr(f"{condition}.colorIfFalseR", 0)
            cmds.setAttr(f"{condition}.colorIfTrueR", 1)


            cmds.connectAttr(f"{condition}.outColorR", f"{parent_matrix_parents}.target[{i}].weight")

    cmds.addAttr(target, longName="TranslateValue", attributeType="float", min=0, max=1, defaultValue=default_translate, keyable=True)
    cmds.addAttr(target, longName="RotateValue", attributeType="float", min=0, max=1, defaultValue=default_rotate, keyable=True)

    cmds.connectAttr(connections, f"{parent_matrix_parents}.inputMatrix")
    cmds.connectAttr(connections, f"{parent_matrix_masterwalk}.inputMatrix")
    cmds.connectAttr(f"{parent_matrix_parents}.outputMatrix", f"{blend_matrix}.target[0].targetMatrix")
    cmds.connectAttr(f"{parent_matrix_masterwalk}.outputMatrix", f"{blend_matrix}.inputMatrix")

    offset_masterwalk = get_offset_matrix(target_grp, masterWalk_ctl)
    cmds.connectAttr(f"{masterWalk_ctl}.worldMatrix[0]", f"{parent_matrix_masterwalk}.target[0].targetMatrix")
    cmds.setAttr(f"{parent_matrix_masterwalk}.target[0].offsetMatrix", offset_masterwalk, type="matrix")

    for z, driver in enumerate(sources):
        off_matrix = get_offset_matrix(target_grp, driver)
        cmds.connectAttr(f"{driver}.worldMatrix[0]", f"{parent_matrix_parents}.target[{z}].targetMatrix") 
        cmds.setAttr(f"{parent_matrix_parents}.target[{z}].offsetMatrix", off_matrix, type="matrix")

    cmds.connectAttr(f"{target}.RotateValue", f"{blend_matrix}.target[0].rotateWeight")
    cmds.connectAttr(f"{target}.TranslateValue", f"{blend_matrix}.target[0].translateWeight")
    cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
    cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)

    cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{target_grp}.offsetParentMatrix", force=True)


def make_spaces_biped():

    data_exporter = data_export.DataExport()


    body_ctl = data_exporter.get_data("C_spineModule", "body_ctl")
    local_hip_ctl = data_exporter.get_data("C_spineModule", "local_hip_ctl")
    local_chest_ctl = data_exporter.get_data("C_spineModule", "local_chest_ctl")

    for side in ["L", "R"]:
        clavicle_ctl = data_exporter.get_data(f"{side}_armModule", f"clavicle_ctl")
        l_shoulder_ctl = data_exporter.get_data(f"{side}_armModule", f"fk_ctl")[0]
        l_armRootIk = data_exporter.get_data(f"{side}_armModule", f"root_ctl")
        l_leg_ctl = data_exporter.get_data(f"{side}_legModule", f"fk_ctl")[0]
        l_legRootIk = data_exporter.get_data(f"{side}_legModule", f"root_ctl")

        fk_switch(target=clavicle_ctl, sources=[local_chest_ctl])
        fk_switch(target=l_shoulder_ctl, sources=[clavicle_ctl, local_chest_ctl])
        fk_switch(target=l_leg_ctl, sources=[local_hip_ctl, body_ctl])
        fk_switch(target=l_armRootIk, sources=[clavicle_ctl, local_chest_ctl, body_ctl])
        fk_switch(target=l_legRootIk, sources=[local_hip_ctl, body_ctl])


def make_spaces_quadruped():

    data_exporter = data_export.DataExport()


    body_ctl = data_exporter.get_data("C_spineModule", "body_ctl")
    local_hip_ctl = data_exporter.get_data("C_spineModule", "local_hip_ctl")
    local_chest_ctl = data_exporter.get_data("C_spineModule", "local_chest_ctl")

    neck = data_exporter.get_data("C_neckModule", "neck_ctl")
    head = data_exporter.get_data("C_neckModule", "head_ctl")

    trunk = data_exporter.get_data("C_trunkModule", "main_ctl")
    print(f"Trunk: {trunk}")

    fk_switch(target=trunk, sources=[head, local_chest_ctl, body_ctl], default_rotate=1, default_translate=1)
    fk_switch(target=neck, sources=[local_chest_ctl, body_ctl])
    fk_switch(target=head, sources=[neck, local_chest_ctl, body_ctl], default_rotate=0, default_translate=1)


    for side in ["L", "R"]:
        scapula = data_exporter.get_data(f"{side}_frontLegModule", f"scapula_ctl")
        shoulder_ctl = data_exporter.get_data(f"{side}_frontLegModule", f"fk_ctl")[0]
        frontLegRootIk = data_exporter.get_data(f"{side}_frontLegModule", f"root_ctl")
        armPv = data_exporter.get_data(f"{side}_frontLegModule", f"pv_ctl")
        frontLegEndIk = data_exporter.get_data(f"{side}_frontLegModule", f"end_ik")
        backLeg_ctl = data_exporter.get_data(f"{side}_backLegModule", f"fk_ctl")[0]
        backLegRootIk = data_exporter.get_data(f"{side}_backLegModule", f"root_ctl")
        backLegPv = data_exporter.get_data(f"{side}_backLegModule", f"pv_ctl")
        backLegEndIk = data_exporter.get_data(f"{side}_backLegModule", f"end_ik")

        fk_switch(target=scapula, sources=[local_chest_ctl])
        fk_switch(target=shoulder_ctl, sources=[scapula, local_chest_ctl])
        fk_switch(target=backLeg_ctl, sources=[local_hip_ctl, body_ctl])
        fk_switch(target=frontLegRootIk, sources=[scapula, local_chest_ctl, body_ctl])
        fk_switch(target=backLegRootIk, sources=[local_hip_ctl, body_ctl])


        fk_switch(target=frontLegEndIk, sources=[scapula, local_chest_ctl, body_ctl], default_rotate=0, default_translate=0)
        fk_switch(target=backLegEndIk, sources=[local_hip_ctl, body_ctl], default_rotate=0, default_translate=0)

        fk_switch(target=armPv, sources=[frontLegEndIk, local_chest_ctl, body_ctl])
        fk_switch(target=backLegPv, sources=[backLegEndIk, local_hip_ctl, body_ctl])
