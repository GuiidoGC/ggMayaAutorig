#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export
from gg_autorig.utils import core
from gg_autorig.utils import basic_structure
import gg_autorig.utils.de_boors_core as de_boors



reload(data_export)

class SpineModule():
    """
    Class to create a spine module in a Maya rigging setup.
    This module handles the creation of spine joints, controllers, and various systems such as stretch, reverse, offset, squash, and volume preservation.
    """
    def __init__(self):
        """
        Initializes the SpineModule class, setting up paths and data exporters.
        
        Args:
            self: Instance of the SpineModule class.
        """
        
        self.data_exporter = data_export.DataExport()

        self.modules_grp = self.data_exporter.get_data("basic_structure", "modules_GRP")
        self.skel_grp = self.data_exporter.get_data("basic_structure", "skel_GRP")
        self.masterWalk_ctl = self.data_exporter.get_data("basic_structure", "masterWalk_CTL")
        self.guides_grp = self.data_exporter.get_data("basic_structure", "guides_GRP")


    def make(self, guide_name):
        """
        Creates the spine module, including the spine chain, controllers, and various systems.

        Args:
            self: Instance of the SpineModule class.
        """

        self.guide_name = guide_name

        self.module_trn = cmds.createNode("transform", name=f"C_spineModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"C_spineControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.skinning_trn = cmds.createNode("transform", name=f"C_spineSkinning_GRP", ss=True, p=self.skel_grp)

        pick_matrix = cmds.createNode("pickMatrix", name="C_spinePickMatrix_PMX", ss=True)
        cmds.connectAttr(f"{self.masterWalk_ctl}.worldMatrix[0]", f"{pick_matrix}.inputMatrix")
        cmds.connectAttr(f"{pick_matrix}.outputMatrix", f"{self.module_trn}.offsetParentMatrix")

        self.create_chain()

        # self.data_exporter.append_data(f"C_spineModule", 
        #                             {"skinning_transform": self.skinning_trn,
        #                             "body_ctl": self.body_ctl,
        #                             "localHip": self.localHip_ctl,
        #                             "localChest": self.localChest_ctl,
        #                             "main_ctl" : self.localHip,
        #                             "end_main_ctl" : self.localChest_ctl
        #                             }
        #                           )

    def create_chain(self):
        """
        Creates the spine joint chain by importing guides and parenting the first joint to the module transform.

        Args:
            self: Instance of the SpineModule class.
        """
        
        self.guides = guide_import(self.guide_name, all_descendents=True, path=None)

        if cmds.attributeQuery("moduleName", node=self.guides[0], exists=True):
            self.enum_str = cmds.attributeQuery("moduleName", node=self.guides[0], listEnum=True)[0]
        cmds.addAttr(self.skinning_trn, longName="moduleName", attributeType="enum", enumName=self.enum_str, keyable=False)


        aim_matrix = cmds.createNode("aimMatrix", name="C_spine01Guide_AMX", ss=True)
        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{aim_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{aim_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{aim_matrix}.primaryInputAxis", 0, 1, 0, type="double3")

        blend_matrix = cmds.createNode("blendMatrix", name="C_spine03Guide_BMX", ss=True)
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].translateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)

        blend_matrix02 = cmds.createNode("blendMatrix", name="C_spine02Guide_BMX", ss=True)
        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{blend_matrix02}.inputMatrix")
        cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{blend_matrix02}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix02}.target[0].weight", 0.5)
        cmds.setAttr(f"{blend_matrix02}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix02}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrix02}.target[0].shearWeight", 0)

        blend_matrixTan_01 = cmds.createNode("blendMatrix", name="C_spine01GuideTan_BMX", ss=True)
        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{blend_matrixTan_01}.inputMatrix")
        cmds.connectAttr(f"{blend_matrix02}.outputMatrix", f"{blend_matrixTan_01}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrixTan_01}.target[0].weight", 0.33333)
        cmds.setAttr(f"{blend_matrixTan_01}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrixTan_01}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrixTan_01}.target[0].shearWeight", 0)

        blend_matrixTan_02 = cmds.createNode("blendMatrix", name="C_spine02GuideTan_BMX", ss=True)
        cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{blend_matrixTan_02}.inputMatrix")
        cmds.connectAttr(f"{blend_matrix02}.outputMatrix", f"{blend_matrixTan_02}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrixTan_02}.target[0].weight", 0.33333)
        cmds.setAttr(f"{blend_matrixTan_02}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrixTan_02}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrixTan_02}.target[0].shearWeight", 0)

        self.main_controllers = []
        self.main_controllers_grp = []

        self.guide_matrix = [aim_matrix, blend_matrix02, blend_matrix]

        for i, matrix in enumerate(self.guide_matrix ):
            ctl, ctl_grp = controller_creator(
                name=f"C_spine0{i+1}",
                suffixes=["GRP", "OFF","ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.parent(ctl_grp[0], self.main_controllers[-1] if self.main_controllers else self.controllers_trn)

            if not i == 0:
                offset_multMatrix = cmds.createNode("multMatrix", name=f"C_spineOffset0{i+1}_MMX", ss=True)
                inverse_matrix = cmds.createNode("inverseMatrix", name=f"C_spineOffset0{i+1}_IMX", ss=True)
                cmds.connectAttr(f"{matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[0]")

                cmds.connectAttr(f"{self.guide_matrix[i-1]}.outputMatrix", f"{inverse_matrix}.inputMatrix")

                cmds.connectAttr(f"{inverse_matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[1]")
        

                cmds.connectAttr(f"{offset_multMatrix}.matrixSum", f"{ctl_grp[0]}.offsetParentMatrix")

                for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                    cmds.setAttr(f"{ctl_grp[0]}.{attr}", 0)

            else:
                cmds.connectAttr(f"{matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")



            self.main_controllers.append(ctl)
            self.main_controllers_grp.append(ctl_grp)

        self.guide_matrix_tan = [blend_matrixTan_01, blend_matrixTan_02]

        self.tan_controllers = []
        self.tan_controllers_grp = []

        for i, matrix in enumerate(self.guide_matrix_tan):
            ctl, ctl_grp = controller_creator(
                name=f"C_spine0{(i+1)*2-1}Tan",
                suffixes=["GRP", "OFF","ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.parent(ctl_grp[0], self.main_controllers[i*2])

            offset_multMatrix = cmds.createNode("multMatrix", name=f"C_spineOffset0{(i+1)*2-1}Tan_MMX", ss=True)
            inverse_matrix = cmds.createNode("inverseMatrix", name=f"C_spineOffset0{(i+1)*2-1}Tan_IMX", ss=True)
            cmds.connectAttr(f"{matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[0]")

            cmds.connectAttr(f"{self.guide_matrix[i*2]}.outputMatrix", f"{inverse_matrix}.inputMatrix")

            cmds.connectAttr(f"{inverse_matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[1]")


            cmds.connectAttr(f"{offset_multMatrix}.matrixSum", f"{ctl_grp[0]}.offsetParentMatrix")

            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                cmds.setAttr(f"{ctl_grp[0]}.{attr}", 0)

            self.tan_controllers.append(ctl)
            self.tan_controllers_grp.append(ctl_grp[0])

        controllers_chain = [f"{self.main_controllers[0]}.worldMatrix[0]", f"{self.tan_controllers[0]}.worldMatrix[0]", f"{self.main_controllers[1]}.worldMatrix[0]", f"{self.tan_controllers[1]}.worldMatrix[0]", f"{self.main_controllers[2]}.worldMatrix[0]"]

        joints = []

        self.twist_number = 5

        for i in range(self.twist_number):
            t = i / (float(self.twist_number) - 1)
            joint = cmds.createNode("joint", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_JNT"), ss=True, parent=self.skinning_trn)

            pointMatrixWeights = de_boors.pointOnCurveWeights(controllers_chain, t, degree=3)

            pma_node = cmds.createNode('plusMinusAverage', name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_PMA"), ss=True)
            cmds.setAttr(f"{pma_node}.operation", 1)

            pointMatrixNode = cmds.createNode("wtAddMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_PMX"), ss=True)
            pointMatrix = f"{pointMatrixNode}.matrixSum"

            # Scale preservation
            for index, (matrix, weight) in enumerate(pointMatrixWeights):
                md = cmds.createNode('multiplyDivide', name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_MDV"), ss=True)
                cmds.setAttr(f"{md}.input2X", weight)
                cmds.setAttr(f"{md}.input2Y", weight)
                cmds.setAttr(f"{md}.input2Z", weight)
                decomposeNode = cmds.createNode("decomposeMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_DCM"), ss=True)
                cmds.connectAttr(f"{matrix}", f"{decomposeNode}.inputMatrix", force=True)
                cmds.connectAttr(f"{decomposeNode}.outputScale", f"{md}.input1", force=True)               

                cmds.connectAttr(f"{md}.output", f"{pma_node}.input3D[{index}]", force=True)

            # Joint positioning
            for index, (matrix, weight) in enumerate(pointMatrixWeights):
                cmds.connectAttr(matrix, f"{pointMatrixNode}.wtMatrix[{index}].matrixIn")
                float_constant = cmds.createNode("floatConstant", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_FLM"), ss=True)
                cmds.setAttr(f"{float_constant}.inFloat", weight)
                cmds.connectAttr(f"{float_constant}.outFloat", f"{pointMatrixNode}.wtMatrix[{index}].weightIn", force=True)
            
            # Joint Tangent Matrix
            tangentMatrixWeights = de_boors.tangentOnCurveWeights(controllers_chain, t, degree=2)

            tangentMatrixNode = cmds.createNode("wtAddMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_WTADD"), ss=True)
            tangentMatrix = f"{tangentMatrixNode}.matrixSum"
            for index, (matrix, weight) in enumerate(tangentMatrixWeights):
                cmds.connectAttr(matrix, f"{tangentMatrixNode}.wtMatrix[{index}].matrixIn")
                float_constant = cmds.createNode("floatConstant", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_FLM"), ss=True)
                cmds.setAttr(f"{float_constant}.inFloat", weight)
                cmds.connectAttr(f"{float_constant}.outFloat", f"{tangentMatrixNode}.wtMatrix[{index}].weightIn", force=True)

            aimMatrixNode = cmds.createNode("aimMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_AMX"), ss=True)
            cmds.connectAttr(pointMatrix, f"{aimMatrixNode}.inputMatrix")
            cmds.connectAttr(tangentMatrix, f"{aimMatrixNode}.primaryTargetMatrix")
            cmds.setAttr(f"{aimMatrixNode}.primaryMode", 1)
            cmds.setAttr(f"{aimMatrixNode}.primaryInputAxis", 1,0,0, type="double3")
            cmds.setAttr(f"{aimMatrixNode}.secondaryInputAxis", 0,1,0, type="double3")
            cmds.setAttr(f"{aimMatrixNode}.secondaryMode", 0)
            aimMatrixOutput = f"{aimMatrixNode}.outputMatrix"

            pickMatrixNode = cmds.createNode("pickMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_PKMX"), ss=True)
            cmds.connectAttr(aimMatrixOutput, f"{pickMatrixNode}.inputMatrix")
            cmds.setAttr(f"{pickMatrixNode}.useScale", False)
            cmds.setAttr(f"{pickMatrixNode}.useShear", False)
            outputMatrix = f"{pickMatrixNode}.outputMatrix"

            decomposeNode = cmds.createNode("decomposeMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_DCM"), ss=True)
            cmds.connectAttr(outputMatrix, f"{decomposeNode}.inputMatrix")

            composeNode = cmds.createNode("composeMatrix", name=controllers_chain[i].replace("_CTL.worldMatrix[0]", "_CPM"), ss=True)
            cmds.connectAttr(f"{decomposeNode}.outputTranslate", f"{composeNode}.inputTranslate")   
            cmds.connectAttr(f"{decomposeNode}.outputRotate", f"{composeNode}.inputRotate")

            cmds.connectAttr(f"{pma_node}.output3D", f"{composeNode}.inputScale", force=True)



            cmds.connectAttr(f"{composeNode}.outputMatrix", f"{joint}.offsetParentMatrix")

            

            joints.append(joint)


cmds.file(new=True, force=True)

core.DataManager.set_guide_data("D:/git/maya/biped_autorig/guides/moana_01.guides")
core.DataManager.set_ctls_data("D:/git/maya/biped_autorig/curves/body_template_01.ctls")

basic_structure.create_basic_structure(asset_name="moana_02")
a = SpineModule().make("C_spine01_GUIDE")
