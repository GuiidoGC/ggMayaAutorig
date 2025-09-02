import maya.cmds as cmds


def bendy_twist(self, twist_number=5, degree=2, blend_chain=["L_shoulderDr_JNT", "L_elbowDr_JNT"], suffix=f"L_upperArm"):
    
    cvMatrices = [self.blend_wm[i], f"{ctl}.worldMatrix[0]", self.blend_wm[i+1]]

    joints = []

    self.twist_number = 5

    for i in range(self.twist_number):
        t = 0.95 if i == self.twist_number - 1 else i / (float(self.twist_number) - 1)
        joint = cmds.createNode("joint", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_JNT", ss=True, parent=self.skinnging_grp)

        pointMatrixWeights = de_boors.pointOnCurveWeights(cvMatrices, t, degree=2)

        pma_node = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}{bendy}0{i+1}_PMA", ss=True)
        cmds.setAttr(f"{pma_node}.operation", 1)

        pointMatrixNode = cmds.createNode("wtAddMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_PMX", ss=True)
        pointMatrix = f"{pointMatrixNode}.matrixSum"

        # Scale preservation
        for index, (matrix, weight) in enumerate(pointMatrixWeights):
            md = cmds.createNode('multiplyDivide', name=f"{self.side}_{self.module_name}{bendy}0{i+1}_MDV", ss=True)
            cmds.setAttr(f"{md}.input2X", weight)
            cmds.setAttr(f"{md}.input2Y", weight)
            cmds.setAttr(f"{md}.input2Z", weight)
            decomposeNode = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_DCM", ss=True)
            cmds.connectAttr(f"{matrix}", f"{decomposeNode}.inputMatrix", force=True)
            cmds.connectAttr(f"{decomposeNode}.outputScale", f"{md}.input1", force=True)               

            cmds.connectAttr(f"{md}.output", f"{pma_node}.input3D[{index}]", force=True)

        # Joint positioning
        for index, (matrix, weight) in enumerate(pointMatrixWeights):
            cmds.connectAttr(matrix, f"{pointMatrixNode}.wtMatrix[{index}].matrixIn")
            float_constant = cmds.createNode("floatConstant", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_FLM", ss=True)
            cmds.setAttr(f"{float_constant}.inFloat", weight)
            cmds.connectAttr(f"{float_constant}.outFloat", f"{pointMatrixNode}.wtMatrix[{index}].weightIn", force=True)
        
        # Joint Tangent Matrix
        tangentMatrixWeights = de_boors.tangentOnCurveWeights(cvMatrices, t, degree=2)

        tangentMatrixNode = cmds.createNode("wtAddMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_WTADD", ss=True)
        tangentMatrix = f"{tangentMatrixNode}.matrixSum"
        for index, (matrix, weight) in enumerate(tangentMatrixWeights):
            cmds.connectAttr(matrix, f"{tangentMatrixNode}.wtMatrix[{index}].matrixIn")
            float_constant = cmds.createNode("floatConstant", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_FLM", ss=True)
            cmds.setAttr(f"{float_constant}.inFloat", weight)
            cmds.connectAttr(f"{float_constant}.outFloat", f"{tangentMatrixNode}.wtMatrix[{index}].weightIn", force=True)

        aimMatrixNode = cmds.createNode("aimMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_AMX", ss=True)
        cmds.connectAttr(pointMatrix, f"{aimMatrixNode}.inputMatrix")
        cmds.connectAttr(tangentMatrix, f"{aimMatrixNode}.primaryTargetMatrix")
        cmds.setAttr(f"{aimMatrixNode}.primaryMode", 1)
        cmds.setAttr(f"{aimMatrixNode}.primaryInputAxis", *self.primary_aim)
        cmds.setAttr(f"{aimMatrixNode}.secondaryInputAxis", *self.secondary_aim)
        cmds.setAttr(f"{aimMatrixNode}.secondaryMode", 0)
        aimMatrixOutput = f"{aimMatrixNode}.outputMatrix"

        pickMatrixNode = cmds.createNode("pickMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_PKMX", ss=True)
        cmds.connectAttr(aimMatrixOutput, f"{pickMatrixNode}.inputMatrix")
        cmds.setAttr(f"{pickMatrixNode}.useScale", False)
        cmds.setAttr(f"{pickMatrixNode}.useShear", False)
        outputMatrix = f"{pickMatrixNode}.outputMatrix"

        decomposeNode = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_DCM", ss=True)
        cmds.connectAttr(outputMatrix, f"{decomposeNode}.inputMatrix")

        composeNode = cmds.createNode("composeMatrix", name=f"{self.side}_{self.module_name}{bendy}0{i+1}_CPM", ss=True)
        cmds.connectAttr(f"{decomposeNode}.outputTranslate", f"{composeNode}.inputTranslate")   
        cmds.connectAttr(f"{decomposeNode}.outputRotate", f"{composeNode}.inputRotate")

        cmds.connectAttr(f"{pma_node}.output3D", f"{composeNode}.inputScale", force=True)



        cmds.connectAttr(f"{composeNode}.outputMatrix", f"{joint}.offsetParentMatrix")

        

        joints.append(joint)

    if "Lower" in bendy:
        joint = cmds.createNode("joint", name=f"{self.side}_{self.module_name}{bendy}0{i+2}_JNT", ss=True, parent=self.skinnging_grp)
        cmds.connectAttr(cvMatrices[-1], f"{joint}.offsetParentMatrix")
        joints.append(joint)