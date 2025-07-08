
from maya import cmds
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.curve_tool import init_template_file
from importlib import reload

# Import DeBoors Core
import gg_autorig.utils.de_boors_core as de_boors
reload(de_boors)

init_template_file("D:/git/maya/biped_autorig/curves/guides_curves_template.json")


class LimbModule(object):













    def bendy_twist(self, pCount=5, degree=2, blend_chain=["L_shoulderNoRoll_JNT", "L_elbowNoRollEnd_JNT"], suffix="L_upperArm"):

        ctl, ctl_grp = controller_creator(suffix, suffixes=["GRP", "ANM"], lock=["v"])

        blend_matrix = cmds.createNode("blendMatrix", name=f"{suffix}_blendMatrix")
        cmds.connectAttr(f"{blend_chain[0]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{blend_chain[1]}.worldMatrix[0]", f"{blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix}.target[0].weight", 0.5)
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)
        cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")



        cvMatrices = [f"{driver}.worldMatrix[0]" for driver in [blend_chain[0], ctl, blend_chain[1]]]

        joints = []

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
                pointMatrixWeights = de_boors.pointOnCurveWeights(cvMatrices, t, degree=degree)

            pma_node = cmds.createNode('plusMinusAverage', name=f"plusMinusAverage0{i+1}")
            cmds.setAttr(f"{pma_node}.operation", 1)
        
            pointMatrixNode = cmds.createNode("wtAddMatrix", name=f"pointMatrix0{i+1}")
            pointMatrix = f"{pointMatrixNode}.matrixSum"
            for index, (matrix, weight) in enumerate(pointMatrixWeights):
                cmds.connectAttr(matrix, f"{pointMatrixNode}.wtMatrix[{index}].matrixIn")
                cmds.setAttr(f"{pointMatrixNode}.wtMatrix[{index}].weightIn", weight)

                md = cmds.createNode('multiplyDivide', name=f"multiplyDivide{index}")
                cmds.setAttr(f"{md}.input2X", weight)
                cmds.setAttr(f"{md}.input2Y", weight)
                cmds.setAttr(f"{md}.input2Z", weight)
                parent = matrix.replace(".worldMatrix[0]", ".scale")
                cmds.connectAttr(f"{parent}", f"{md}.input1", force=True)
                cmds.connectAttr(f"{md}.output", f"{pma_node}.input3D[{index}]", force=True)
            
            tangentMatrixWeights = de_boors.tangentOnCurveWeights(cvMatrices, t, degree=degree)
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

            cmds.connectAttr(f"{pma_node}.output3D", f"{composeNode}.inputScale", force=True)



            cmds.connectAttr(f"{composeNode}.outputMatrix", f"{pNode}.offsetParentMatrix")

            joints.append(pNode)


a = LimbModule()
a.bendy_twist()
