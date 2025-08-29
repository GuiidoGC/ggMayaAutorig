import maya.cmds as cmds

matrix_nodes = []
for i in range(1, 11):
    percentatge = (i-1) / len(range(1, 11))
    motionPath = cmds.createNode("motionPath", name=f"R_ear0{i}_MPA", ss=True)
    cmds.connectAttr(f"R_ear_CRVShape.worldSpace[0]", f"{motionPath}.geometryPath", force=True)


    matrix_node = cmds.createNode('fourByFourMatrix', name=f"R_ear0{i}_4B4M", ss=True)


    cmds.connectAttr(f"{motionPath}.allCoordinates.xCoordinate", f"{matrix_node}.in30", force=True)
    cmds.connectAttr(f"{motionPath}.allCoordinates.yCoordinate", f"{matrix_node}.in31", force=True)
    cmds.connectAttr(f"{motionPath}.allCoordinates.zCoordinate", f"{matrix_node}.in32", force=True)

    # cmds.setAttr(f"{point_on_surface}.turnOnPercentage", 1)
    cmds.setAttr(f"{motionPath}.uValue", percentatge)

    matrix_nodes.append(matrix_node)


for i, matrix in enumerate(matrix_nodes):
    aimMatrix = cmds.createNode("aimMatrix", name=f"R_ear0{i}_AMX", ss=True)
    cmds.connectAttr(f"{matrix}.output", f"{aimMatrix}.inputMatrix", force=True)
    try:
        cmds.connectAttr(f"{matrix_nodes[i + 1]}.output", f"{aimMatrix}.primaryTargetMatrix", force=True)
        cmds.setAttr(f"{aimMatrix}.primaryInputAxis", -1, 0, 0, type="double3")

    except IndexError:
        cmds.connectAttr(f"{matrix_nodes[i - 1]}.output", f"{aimMatrix}.primaryTargetMatrix", force=True)
        cmds.setAttr(f"{aimMatrix}.primaryInputAxis", 1, 0, 0, type="double3")

    joint = cmds.createNode("joint", name=f"R_ear0{i}_JNT", ss=True)
    cmds.connectAttr(f"{aimMatrix}.outputMatrix", f"{joint}.offsetParentMatrix", force=True)