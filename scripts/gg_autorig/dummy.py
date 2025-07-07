def defaultKnots(count, degree=3):
    knots = [0 for i in range(degree)] + [i for i in range(count - degree + 1)]
    knots += [count - degree for i in range(degree)]
    return [float(knot) for knot in knots]


def pointOnCurveWeights(cvs, t, degree, knots=None):
    order = degree + 1
    if len(cvs) <= degree:
        raise CurveException(f"Curves of degree {degree} require at least {degree + 1} cvs")

    knots = knots or defaultKnots(len(cvs), degree)
    if len(knots) != len(cvs) + order:
        raise CurveException(f"Not enough knots provided. Curves with {len(cvs)} cvs must have a knot vector of length {len(cvs) + order}. "
                             f"Received a knot vector of length {len(knots)}: {knots}. "
                             "Total knot count must equal len(cvs) + degree + 1.")

    _cvs = cvs
    cvs = [i for i in range(len(cvs))]

    min = knots[order] - 1
    max = knots[len(knots) - 1 - order] + 1
    t = (t * (max - min)) + min

    segment = degree
    for index, knot in enumerate(knots[order:len(knots) - order]):
        if knot <= t:
            segment = index + order

    cvs = [cvs[j + segment - degree] for j in range(0, degree + 1)]

    cvWeights = [{cv: 1.0} for cv in cvs]
    for r in range(1, degree + 1):
        for j in range(degree, r - 1, -1):
            right = j + 1 + segment - r
            left = j + segment - degree
            alpha = (t - knots[left]) / (knots[right] - knots[left])

            weights = {}
            for cv, weight in cvWeights[j].items():
                weights[cv] = weight * alpha

            for cv, weight in cvWeights[j - 1].items():
                if cv in weights:
                    weights[cv] += weight * (1 - alpha)
                else:
                    weights[cv] = weight * (1 - alpha)

            cvWeights[j] = weights

    cvWeights = cvWeights[degree]
    return [[_cvs[index], weight] for index, weight in cvWeights.items()]


def tangentOnCurveWeights(cvs, t, degree, knots=None):
    order = degree + 1
    if len(cvs) <= degree:
        raise CurveException(f"Curves of degree {degree} require at least {degree + 1} cvs")

    knots = knots or defaultKnots(len(cvs), degree)
    if len(knots) != len(cvs) + order:
        raise CurveException(f"Not enough knots provided. Curves with {len(cvs)} cvs must have a knot vector of length {len(cvs) + order}. "
                             f"Received a knot vector of length {len(knots)}: {knots}. "
                             "Total knot count must equal len(cvs) + degree + 1.")

    min = knots[order] - 1
    max = knots[len(knots) - 1 - order] + 1
    t = (t * (max - min)) + min

    segment = degree
    for index, knot in enumerate(knots[order:len(knots) - order]):
        if knot <= t:
            segment = index + order

    _cvs = cvs
    cvs = [i for i in range(len(cvs))]

    degree -= 1
    qWeights = [{cv: 1.0} for cv in range(0, degree + 1)]

    for r in range(1, degree + 1):
        for j in range(degree, r - 1, -1):
            right = j + 1 + segment - r
            left = j + segment - degree
            alpha = (t - knots[left]) / (knots[right] - knots[left])

            weights = {}
            for cv, weight in qWeights[j].items():
                weights[cv] = weight * alpha

            for cv, weight in qWeights[j - 1].items():
                if cv in weights:
                    weights[cv] += weight * (1 - alpha)
                else:
                    weights[cv] = weight * (1 - alpha)

            qWeights[j] = weights
    weights = qWeights[degree]

    cvWeights = []
    for j in range(0, degree + 1):
        weight = weights[j]
        cv0 = j + segment - degree
        cv1 = j + segment - degree - 1
        alpha = weight * (degree + 1) / (knots[j + segment + 1] - knots[j + segment - degree])
        cvWeights.append([cvs[cv0], alpha])
        cvWeights.append([cvs[cv1], -alpha])

    return [[_cvs[index], weight] for index, weight in cvWeights]


def pointOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    matrixWeightRows = [pointOnCurveWeights(row, u, degree, uKnots) for row in cvs]
    matrixWeightColumns = pointOnCurveWeights([i for i in range(len(matrixWeightRows))], v, degree, vKnots)
    surfaceMatrixWeights = []
    for index, weight in matrixWeightColumns:
        matrixWeights = matrixWeightRows[index]
        surfaceMatrixWeights.extend([[m, (w * weight)] for m, w in matrixWeights])

    return surfaceMatrixWeights


def tangentUOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    matrixWeightRows = [pointOnCurveWeights(row, u, degree, uKnots) for row in cvs]
    matrixWeightColumns = tangentOnCurveWeights([i for i in range(len(matrixWeightRows))], v, degree, vKnots)
    surfaceMatrixWeights = []
    for index, weight in matrixWeightColumns:
        matrixWeights = matrixWeightRows[index]
        surfaceMatrixWeights.extend([[m, (w * weight)] for m, w in matrixWeights])

    return surfaceMatrixWeights


def tangentVOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    rowCount = len(cvs)
    columnCount = len(cvs[0])
    reorderedCvs = [[cvs[row][col] for row in range(rowCount)] for col in range(columnCount)]
    return tangentUOnSurfaceWeights(reorderedCvs, v, u, uKnots=vKnots, vKnots=uKnots, degree=degree)


class CurveException(BaseException):
    pass


import math
from maya import cmds
import maya.api.OpenMaya as om
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.curve_tool import init_template_file
from gg_autorig.utils.space_switch import switch_matrix_space

init_template_file("D:/git/maya/biped_autorig/curves/guides_curves_template.json")

def _testMatrixOnCurve(count=3, pCount=5, degree=2, blend_chain=["L_shoulderNoRoll_JNT", "L_elbowNoRollEnd_JNT"], suffix="L_upperArm"):
    pCount = pCount or count * 4

    ctl, ctl_grp = controller_creator(suffix, suffixes=["GRP", "ANM"], lock=["v"])
    cmds.delete(cmds.parentConstraint(blend_chain[0], blend_chain[1], ctl_grp[0], maintainOffset=False))
    switch_matrix_space(target=ctl, sources=[blend_chain[0]])

    cvMatrices = [f"{driver}.worldMatrix[0]" for driver in [blend_chain[0], ctl, blend_chain[1]]]

    joints = []
    composes = []

    for i in range(pCount):
        t = i / (float(pCount) - 1)
        cmds.select(clear=True)
        pNode = cmds.joint(name=f"pJoint{i}")
        cube = cmds.polyCube(name=f"pJoint{i}_cube", width=1, height=1, depth=1)[0]   
        cmds.parent(cube, pNode)

        if i == pCount - 1:
            weights = [0.0] * len(cvMatrices)
            weights[-1] = 0.95
            if len(cvMatrices) > 1:
                weights[-2] = 0.05
            pointMatrixWeights = [[cvMatrices[j], weights[j]] for j in range(len(cvMatrices))]
        else:
            pointMatrixWeights = pointOnCurveWeights(cvMatrices, t, degree=degree)

        pointMatrixNode = cmds.createNode("wtAddMatrix", name=f"pointMatrix0{i+1}")
        pointMatrix = f"{pointMatrixNode}.matrixSum"
        for index, (matrix, weight) in enumerate(pointMatrixWeights):
            cmds.connectAttr(matrix, f"{pointMatrixNode}.wtMatrix[{index}].matrixIn")
            cmds.setAttr(f"{pointMatrixNode}.wtMatrix[{index}].weightIn", weight)

        tangentMatrixWeights = tangentOnCurveWeights(cvMatrices, t, degree=degree)
        tangentMatrixNode = cmds.createNode("wtAddMatrix", name=f"tangentMatrix0{i+1}")
        tangentMatrix = f"{tangentMatrixNode}.matrixSum"
        for index, (matrix, weight) in enumerate(tangentMatrixWeights):
            cmds.connectAttr(matrix, f"{tangentMatrixNode}.wtMatrix[{index}].matrixIn")
            cmds.setAttr(f"{tangentMatrixNode}.wtMatrix[{index}].weightIn", weight)

        aimMatrixNode = cmds.createNode("aimMatrix", name=f"aimMatrix0{i+1}")
        cmds.connectAttr(pointMatrix, f"{aimMatrixNode}.inputMatrix")
        cmds.connectAttr(tangentMatrix, f"{aimMatrixNode}.primaryTargetMatrix")
        cmds.setAttr(f"{aimMatrixNode}.primaryMode", 1)
        cmds.setAttr(f"{aimMatrixNode}.primaryInputAxis", 1, 0, 0)
        cmds.setAttr(f"{aimMatrixNode}.secondaryInputAxis", 0, 1, 0)
        cmds.setAttr(f"{aimMatrixNode}.secondaryMode", 0)
        aimMatrixOutput = f"{aimMatrixNode}.outputMatrix"

        pickMatrixNode = cmds.createNode("pickMatrix", name=f"noScale0{i+1}")
        cmds.connectAttr(aimMatrixOutput, f"{pickMatrixNode}.inputMatrix")
        cmds.setAttr(f"{pickMatrixNode}.useScale", False)
        cmds.setAttr(f"{pickMatrixNode}.useShear", False)
        outputMatrix = f"{pickMatrixNode}.outputMatrix"

        decomposeNode = cmds.createNode("decomposeMatrix", name=f"decomposeMatrix0{i+1}")
        cmds.connectAttr(outputMatrix, f"{decomposeNode}.inputMatrix")

        composeNode = cmds.createNode("composeMatrix", name=f"composeMatrix0{i+1}")
        cmds.connectAttr(f"{decomposeNode}.outputTranslate", f"{composeNode}.inputTranslate")   
        cmds.connectAttr(f"{decomposeNode}.outputRotate", f"{composeNode}.inputRotate")

        composes.append(composeNode)



        cmds.connectAttr(f"{composeNode}.outputMatrix", f"{pNode}.offsetParentMatrix")

        joints.append(pNode)

    volume_preservation_setup(joints=joints, controllers=[blend_chain[0], ctl, blend_chain[1]], prefix="volPres_", composeNodes=composes)

def volume_preservation_setup(joints, controllers, prefix='volPres_', composeNodes=[None]):

    # Get controller world positions
    ctrl_positions = [om.MVector(*cmds.xform(ctrl, q=True, ws=True, t=True)) for ctrl in controllers]

    for i, jnt in enumerate(joints):
        jnt_pos = om.MVector(*cmds.xform(jnt, q=True, ws=True, t=True))

        # Calculate distances to controllers
        dists = [(i, (jnt_pos - ctrl_positions[i]).length()) for i in range(3)]
        dists.sort(key=lambda x: x[1])  # sort by distance

        # Take 2 closest controllers
        (i1, d1), (i2, d2) = dists[0], dists[1]

        # Compute inverse-distance weights
        inv1 = 1.0 / d1 if d1 > 1e-4 else 1e6
        inv2 = 1.0 / d2 if d2 > 1e-4 else 1e6
        total = inv1 + inv2
        w1 = inv1 / total
        w2 = inv2 / total

        # Create output blend node
        pma_node = cmds.createNode('plusMinusAverage', name=f"{prefix}{jnt}_pma")
        cmds.setAttr(f"{pma_node}.operation", 1)  # sum

        # Connect first closest controller
        md1 = cmds.createNode('multiplyDivide', name=f"{prefix}{jnt}_md{i1}")
        cmds.setAttr(f"{md1}.input2X", w1)
        cmds.setAttr(f"{md1}.input2Y", w1)
        cmds.setAttr(f"{md1}.input2Z", w1)
        cmds.connectAttr(f"{controllers[i1]}.scale", f"{md1}.input1", force=True)
        cmds.connectAttr(f"{md1}.output", f"{pma_node}.input3D[0]", force=True)

        # Connect second closest controller
        md2 = cmds.createNode('multiplyDivide', name=f"{prefix}{jnt}_md{i2}")
        cmds.setAttr(f"{md2}.input2X", w2)
        cmds.setAttr(f"{md2}.input2Y", w2)
        cmds.setAttr(f"{md2}.input2Z", w2)
        cmds.connectAttr(f"{controllers[i2]}.scale", f"{md2}.input1", force=True)
        cmds.connectAttr(f"{md2}.output", f"{pma_node}.input3D[1]", force=True)

        # Connect final blended scale to the joint
        cmds.connectAttr(f"{pma_node}.output3D", f"{composeNodes[i]}.inputScale", force=True)



print("Run the following commands to test the curve functions:")
_testMatrixOnCurve()
