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

