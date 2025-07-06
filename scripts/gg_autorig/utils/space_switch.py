import maya.cmds as cmds
import maya.api.OpenMaya as om

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
