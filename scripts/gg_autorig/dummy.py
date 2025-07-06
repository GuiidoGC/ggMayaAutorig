def defaultKnots(count, degree=3):
    """
    Gets a default knot vector for a given number of cvs and degrees.

    Args:
        count(int): The number of cvs. 
        degree(int): The curve degree. 

    Returns:
        list: A list of knot values.
    """
    knots = [0 for i in range(degree)] + [i for i in range(count - degree + 1)]
    knots += [count - degree for i in range(degree)]
    return [float(knot) for knot in knots]


def pointOnCurveWeights(cvs, t, degree, knots=None):
    """
    Creates a mapping of cvs to curve weight values on a spline curve.
    While all cvs are required, only the cvs with non-zero weights will be returned.
    This function is based on de Boor's algorithm for evaluating splines and has been modified to consolidate weights.

    Args:
        cvs(list): A list of cvs, these are used for the return value.
        t(float): A parameter value. 
        degree(int): The curve dimensions. 
        knots(list): A list of knot values. 

    Returns:
        list: A list of control point, weight pairs.
    """

    order = degree + 1  # Our functions often use order instead of degree
    if len(cvs) <= degree:
        raise CurveException('Curves of degree %s require at least %s cvs' % (degree, degree + 1))

    knots = knots or defaultKnots(len(cvs), degree)  # Defaults to even knot distribution
    if len(knots) != len(cvs) + order:
        raise CurveException('Not enough knots provided. Curves with %s cvs must have a knot vector of length %s. '
                             'Received a knot vector of length %s: %s. '
                             'Total knot count must equal len(cvs) + degree + 1.' % (len(cvs), len(cvs) + order,
                                                                                     len(knots), knots))

    # Convert cvs into hash-able indices
    _cvs = cvs
    cvs = [i for i in range(len(cvs))]

    # Remap the t value to the range of knot values.
    min = knots[order] - 1
    max = knots[len(knots) - 1 - order] + 1
    t = (t * (max - min)) + min

    # Determine which segment the t lies in
    segment = degree
    for index, knot in enumerate(knots[order:len(knots) - order]):
        if knot <= t:
            segment = index + order

    # Filter out cvs we won't be using
    cvs = [cvs[j + segment - degree] for j in range(0, degree + 1)]

    # Run a modified version of de Boors algorithm
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
    """
    Creates a mapping of cvs to curve tangent weight values.
    While all cvs are required, only the cvs with non-zero weights will be returned.

    Args:
        cvs(list): A list of cvs, these are used for the return value.
        t(float): A parameter value. 
        degree(int): The curve dimensions. 
        knots(list): A list of knot values. 

    Returns:
        list: A list of control point, weight pairs.
    """

    order = degree + 1  # Our functions often use order instead of degree
    if len(cvs) <= degree:
        raise CurveException('Curves of degree %s require at least %s cvs' % (degree, degree + 1))

    knots = knots or defaultKnots(len(cvs), degree)  # Defaults to even knot distribution
    if len(knots) != len(cvs) + order:
        raise CurveException('Not enough knots provided. Curves with %s cvs must have a knot vector of length %s. '
                             'Received a knot vector of length %s: %s. '
                             'Total knot count must equal len(cvs) + degree + 1.' % (len(cvs), len(cvs) + order,
                                                                                     len(knots), knots))

    # Remap the t value to the range of knot values.
    min = knots[order] - 1
    max = knots[len(knots) - 1 - order] + 1
    t = (t * (max - min)) + min

    # Determine which segment the t lies in
    segment = degree
    for index, knot in enumerate(knots[order:len(knots) - order]):
        if knot <= t:
            segment = index + order

    # Convert cvs into hash-able indices
    _cvs = cvs
    cvs = [i for i in range(len(cvs))]

    # In order to find the tangent we need to find points on a lower degree curve
    degree = degree - 1
    qWeights = [{cv: 1.0} for cv in range(0, degree + 1)]

    # Get the DeBoor weights for this lower degree curve
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

    # Take the lower order weights and match them to our actual cvs
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
    """
    Creates a mapping of cvs to surface point weight values.

    Args:
        cvs(list): A list of cv rows, these are used for the return value.
        u(float): The u parameter value on the curve.
        v(float): The v parameter value on the curve.
        uKnots(list, optional): A list of knot integers along u.
        vKnots(list, optional): A list of knot integers along v.
        degree(int, optional): The degree of the curve. Minimum is 2.

    Returns:
        list: A list of control point, weight pairs.
    """
    matrixWeightRows = [pointOnCurveWeights(row, u, degree, uKnots) for row in cvs]
    matrixWeightColumns = pointOnCurveWeights([i for i in range(len(matrixWeightRows))], v, degree, vKnots)
    surfaceMatrixWeights = []
    for index, weight in matrixWeightColumns:
        matrixWeights = matrixWeightRows[index]
        surfaceMatrixWeights.extend([[m, (w * weight)] for m, w in matrixWeights])

    return surfaceMatrixWeights


def tangentUOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    """
    Creates a mapping of cvs to surface tangent weight values along the u axis.

    Args:
        cvs(list): A list of cv rows, these are used for the return value.
        u(float): The u parameter value on the curve.
        v(float): The v parameter value on the curve.
        uKnots(list, optional): A list of knot integers along u.
        vKnots(list, optional): A list of knot integers along v.
        degree(int, optional): The degree of the curve. Minimum is 2.

    Returns:
        list: A list of control point, weight pairs.
    """

    matrixWeightRows = [pointOnCurveWeights(row, u, degree, uKnots) for row in cvs]
    matrixWeightColumns = tangentOnCurveWeights([i for i in range(len(matrixWeightRows))], v, degree, vKnots)
    surfaceMatrixWeights = []
    for index, weight in matrixWeightColumns:
        matrixWeights = matrixWeightRows[index]
        surfaceMatrixWeights.extend([[m, (w * weight)] for m, w in matrixWeights])

    return surfaceMatrixWeights


def tangentVOnSurfaceWeights(cvs, u, v, uKnots=None, vKnots=None, degree=3):
    """
    Creates a mapping of cvs to surface tangent weight values along the v axis.

    Args:
        cvs(list): A list of cv rows, these are used for the return value.
        u(float): The u parameter value on the curve.
        v(float): The v parameter value on the curve.
        uKnots(list, optional): A list of knot integers along u.
        vKnots(list, optional): A list of knot integers along v.
        degree(int, optional): The degree of the curve. Minimum is 2.

    Returns:
        list: A list of control point, weight pairs.
    """
    # Re-order the cvs
    rowCount = len(cvs)
    columnCount = len(cvs[0])
    reorderedCvs = [[cvs[row][col] for row in xrange(rowCount)] for col in xrange(columnCount)]
    return tangentUOnSurfaceWeights(reorderedCvs, v, u, uKnots=vKnots, vKnots=uKnots, degree=degree)


class CurveException(BaseException):
    """ Raised to indicate invalid curve parameters. """


# ------- EXAMPLES -------- #


import math
from maya import cmds
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.curve_tool import init_template_file
from gg_autorig.utils.space_switch import switch_matrix_space

init_template_file("D:/git/maya/biped_autorig/curves/guides_curves_template.json")

def _testMatrixOnCurve(count=3, pCount=5, degree=2, blend_chain=["L_shoulder_JNT", "L_elbow_JNT"], suffix = "L_upperArm"):
    """
    Creates an example curve with the given cv and point counts.
    
    Args:
        count(int): The amount of cvs. 
        pCount(int): The amount of points to attach to the curve.
        degree(int): The degree of the curve.
    """

    pCount = pCount or count * 4

    # Create the control points
    ctl, ctl_grp = controller_creator(suffix, suffixes=["GRP", "ANM"])
    cmds.delete(cmds.parentConstraint(blend_chain[0], blend_chain[1], ctl_grp[0], maintainOffset=False))
    switch_matrix_space(target = ctl, sources  =[blend_chain[0]])
    

    cvMatrices = []
    for driver in [blend_chain[0], ctl, blend_chain[1]]:

        cvMatrices.append(f"{driver}.worldMatrix[0]") 

    # Attach the cubes
    for i in range(pCount):
        t = i / (float(pCount) - 1)
        cmds.select(clear=True)
        pNode = cmds.joint(name='pJoint%s' % i)

        # Create the position matrix
        if i == pCount - 1:
            # For the last joint, use custom weights: 0.95 for last cv, 0.05 for second last, 0 for others
            weights = [0.0] * len(cvMatrices)
            weights[-1] = 0.95
            if len(cvMatrices) > 1:
                weights[-2] = 0.05
            pointMatrixWeights = [[cvMatrices[j], weights[j]] for j in range(len(cvMatrices))]
        else:
            pointMatrixWeights = pointOnCurveWeights(cvMatrices, t, degree=degree)
        pointMatrixNode = cmds.createNode('wtAddMatrix', name='pointMatrix0%s' % (i+1))
        pointMatrix = '%s.matrixSum' % pointMatrixNode
        for index, (matrix, weight) in enumerate(pointMatrixWeights):
            cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (pointMatrixNode, index))
            cmds.setAttr('%s.wtMatrix[%s].weightIn' % (pointMatrixNode, index), weight)

        # Create the tangent matrix
        tangentMatrixWeights = tangentOnCurveWeights(cvMatrices, t, degree=degree)
        tangentMatrixNode = cmds.createNode('wtAddMatrix', name='tangentMatrix0%s' % (i+1))
        tangentMatrix = '%s.matrixSum' % tangentMatrixNode
        for index, (matrix, weight) in enumerate(tangentMatrixWeights):
            cmds.connectAttr(matrix, '%s.wtMatrix[%s].matrixIn' % (tangentMatrixNode, index))
            cmds.setAttr('%s.wtMatrix[%s].weightIn' % (tangentMatrixNode, index), weight)

        # Create an aim matrix node
        aimMatrixNode = cmds.createNode('aimMatrix', name='aimMatrix0%s' % (i+1))
        cmds.connectAttr(pointMatrix, '%s.inputMatrix' % aimMatrixNode)
        cmds.connectAttr(tangentMatrix, '%s.primaryTargetMatrix' % aimMatrixNode)
        cmds.setAttr('%s.primaryMode' % aimMatrixNode, 1)
        cmds.setAttr('%s.primaryInputAxis' % aimMatrixNode, 1, 0, 0)
        cmds.setAttr('%s.secondaryInputAxis' % aimMatrixNode, 0, 1, 0)
        cmds.setAttr('%s.secondaryMode' % aimMatrixNode, 0)
        aimMatrixOutput = '%s.outputMatrix' % aimMatrixNode

        # Remove scale
        pickMatrixNode = cmds.createNode('pickMatrix', name='noScale0%s' % (i+1))
        cmds.connectAttr(aimMatrixOutput, '%s.inputMatrix' % pickMatrixNode)
        cmds.setAttr('%s.useScale' % pickMatrixNode, False)
        cmds.setAttr('%s.useShear' % pickMatrixNode, False)
        outputMatrix = '%s.outputMatrix' % pickMatrixNode

        cmds.connectAttr(outputMatrix, '%s.offsetParentMatrix' % pNode)
       


print('Run the following commands to test the curve functions:')
_testMatrixOnCurve()

