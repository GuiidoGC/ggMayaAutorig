#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export

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
        self.skelHierarchy_grp = self.data_exporter.get_data("basic_structure", "skeletonHierarchy_GRP")


    def make(self):
        """
        Creates the spine module, including the spine chain, controllers, and various systems.

        Args:
            self: Instance of the SpineModule class.
        """

        self.module_trn = cmds.createNode("transform", name=f"C_spineModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"C_spineControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.skinning_trn = cmds.createNode("transform", name=f"C_spineSkinning_GRP", ss=True, p=self.skel_grp)

        self.create_chain()


        # self.data_exporter.append_data(f"C_spineModule", 
        #                             {"lastSpineJnt": self.sub_spine_joints[-1],
        #                             "localChest": self.localChest_ctl,
        #                             "localHip": self.spine_hip_ctl,
        #                             "body" : self.body_ctl,
        #                             "body_grp" : self.body_ctl_grp,
        #                             "spine_ctl" : self.spine_ctl,
        #                             }
        #                           )

    def create_chain(self):
        """
        Creates the spine joint chain by importing guides and parenting the first joint to the module transform.

        Args:
            self: Instance of the SpineModule class.
        """
        
        self.guides = guide_import(f"C_spine01_GUIDE", all_descendents=True, path=None)

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

        # Create the spine joints based on the guides

        pos1 = cmds.xform(self.main_controllers[0], q=True, ws=True, t=True)
        pos2 = cmds.xform(self.main_controllers[-1], q=True, ws=True, t=True)

        vector = [pos2[i] - pos1[i] for i in range(3)]
        distance = math.sqrt(sum([(vector[i])**2 for i in range(3)]))

        num_joints = 5

        self.main_chain = []
        for i in range(num_joints):
            t = float(i) / (num_joints - 1)
            joint_pos = [pos1[j] + vector[j] * t for j in range(3)]
            joint = cmds.joint(name=f"C_spine0{i+1}_JNT", p=joint_pos)
            self.main_chain.append(joint)

        cmds.parent(self.main_chain[0], self.module_trn)

        self.ik_handle, self.effector, self.curve = cmds.ikHandle(
            name="C_spineIk_HDL",
            startJoint=self.main_chain[0],
            endEffector=self.main_chain[-1],
            solver="ikSplineSolver",
            numSpans=2,
            createCurve=True,
            parentCurve=False
        )

        self.curve =cmds.rename(self.curve, "C_spineIkCurve_CRV")

        for i, ctl in enumerate([self.main_controllers[0], self.tan_controllers[0], self.main_controllers[1], self.tan_controllers[1], self.main_controllers[2]]):
            dcp = cmds.createNode("decomposeMatrix", name=ctl.replace("_CTL", "_DCP"), ss=True)
            cmds.connectAttr(f"{ctl}.worldMatrix[0]", f"{dcp}.inputMatrix")
            cmds.connectAttr(f"{dcp}.outputTranslate", f"{self.curve}.controlPoints[{i}]")

        cmds.select(clear=True)
        self.chest_fix = cmds.joint(name = "C_localChest_JNT")
        cmds.parent(self.chest_fix, self.ik_handle, self.curve, self.module_trn)
        self.localChest_ctl, localChest_grp = controller_creator(
            name="C_localChest",
            suffixes=["GRP", "ANM"],
            lock=["scaleX", "scaleY", "scaleZ", "visibility"],
            ro=True,
            parent=self.controllers_trn
        )

        blend_matrix_localChest = cmds.createNode("blendMatrix", name="C_localChest_BMX", ss=True)
        cmds.connectAttr(f"{self.main_controllers[-1]}.worldMatrix[0]", f"{blend_matrix_localChest}.inputMatrix")
        cmds.connectAttr(f"{self.main_chain[-1]}.worldMatrix[0]", f"{blend_matrix_localChest}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix_localChest}.target[0].shearWeight", 0)
        cmds.setAttr(f"{blend_matrix_localChest}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrix_localChest}.target[0].scaleWeight", 0)
        cmds.connectAttr(f"{blend_matrix_localChest}.outputMatrix", f"{localChest_grp[0]}.offsetParentMatrix")
        cmds.connectAttr(f"{self.localChest_ctl}.worldMatrix[0]", f"{self.chest_fix}.offsetParentMatrix")



        # self.spine_hip_ctl, self.spine_hip_ctl_grp = curve_tool.controller_creator(f"C_localHip", suffixes = ["GRP"])
        # position, rotation = guides_manager.guide_import(joint_name=f"C_localHip")

        # cmds.matchTransform(self.spine_hip_ctl_grp[0], self.blend_chain[0], pos=True, rot=True)
        # cmds.xform(self.spine_hip_ctl_grp[0], ws=True, translation=position)
        
        # self.lock_attr(self.spine_hip_ctl)
        # self.lock_attr(self.localChest_ctl)

        # self.body_ctl, self.body_ctl_grp = curve_tool.controller_creator(f"C_body", suffixes = ["GRP"])
        # cmds.matchTransform(self.body_ctl_grp[0], self.spine_grp[0][0])

        # cmds.parent(self.spine_grp[0][0], self.spine_grp[2][0], self.body_ctl) 

        # self.lock_attr(self.body_ctl)