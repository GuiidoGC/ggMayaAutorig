#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export

import gg_autorig.utils.de_boor_core_002 as de_boors_002
from gg_autorig.utils import space_switch as ss
from gg_autorig.utils import core
from gg_autorig.utils import basic_structure


reload(data_export)

AXIS_VECTOR = {'x': (1, 0, 0), '-x': (-1, 0, 0), 'y': (0, 1, 0), '-y': (0, -1, 0), 'z': (0, 0, 1), '-z': (0, 0, -1)}

class NeckModule():
    """
    Class to create a neck module in a Maya rigging setup.
    This module handles the creation of neck joints, controllers, and various systems such as stretch, reverse, offset, squash, and volume preservation.
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
        Creates the neck module, including the neck chain, controllers, and various systems.

        Args:
            self: Instance of the SpineModule class.
        """

        self.guide_name = guide_name
        
        self.side = self.guide_name.split("_")[0]

        self.module_trn = cmds.createNode("transform", name=f"{self.side}_neckModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"{self.side}_neckControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.skinning_trn = cmds.createNode("transform", name=f"{self.side}_neckSkinning_GRP", ss=True, p=self.skel_grp)

        pick_matrix = cmds.createNode("pickMatrix", name=f"{self.side}_neckPickMatrix_PMX", ss=True)
        cmds.connectAttr(f"{self.masterWalk_ctl}.worldMatrix[0]", f"{pick_matrix}.inputMatrix")
        cmds.connectAttr(f"{pick_matrix}.outputMatrix", f"{self.module_trn}.offsetParentMatrix")

        self.primary_aim_vector = om.MVector(AXIS_VECTOR[self.primary_aim])
        self.secondary_aim_vector = om.MVector(AXIS_VECTOR[self.secondary_aim])

        self.create_chain()

        self.data_exporter.append_data(f"{self.side}_neckModule", 
                                    {"skinning_transform": self.skinning_trn,
                                     "neck_ctl": self.main_controllers[0],
                                     "head_ctl": self.main_controllers[1],
                                     "main_ctl" : self.main_controllers[0],
                                     "end_main_ctl" : self.main_controllers[1]
                                    }
                                  )

        

    def create_chain(self):
        """
        Creates the neck joint chain by importing guides and parenting the first joint to the module transform.

        Args:
            self: Instance of the SpineModule class.
        """
        
        self.guides = guide_import(self.guide_name, all_descendents=True, path=None)

        if cmds.attributeQuery("moduleName", node=self.guides[0], exists=True):
            self.enum_str = cmds.attributeQuery("moduleName", node=self.guides[0], listEnum=True)[0]
        cmds.addAttr(self.skinning_trn, longName="moduleName", attributeType="enum", enumName=self.enum_str, keyable=False)

        aim_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_neck01Guide_AMX", ss=True)
        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{aim_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{aim_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{aim_matrix}.primaryInputAxis", *self.primary_aim_vector, type="double3")
        cmds.setAttr(f"{aim_matrix}.secondaryInputAxis", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{aim_matrix}.secondaryTargetVector", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{aim_matrix}.secondaryMode", 2)


   
        self.main_controllers = []
        self.main_controllers_grp = []

        self.guide_matrix = [f"{aim_matrix}.outputMatrix", f"{self.guides[-1]}.worldMatrix[0]"]
        name = ["neck", "head"]

        for i, matrix in enumerate(self.guide_matrix ):
            ctl, ctl_grp = controller_creator(
                name=f"{self.side}_{name[i]}",
                suffixes=["GRP", "OFF","ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
                parent=self.controllers_trn
            )


            cmds.connectAttr(f"{matrix}", f"{ctl_grp[0]}.offsetParentMatrix")

            self.main_controllers.append(ctl)
            self.main_controllers_grp.append(ctl_grp)

        cmds.addAttr(self.main_controllers[1], shortName="STRETCH", niceName="Stretch ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.main_controllers[1]+".STRETCH", channelBox=True, lock=True)
        cmds.addAttr(self.main_controllers[1], shortName="stretch", niceName="Stretch", maxValue=1, minValue=0,defaultValue=0, keyable=True)

        cmds.addAttr(self.main_controllers[1], shortName="attachedFk", niceName="Fk ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.main_controllers[1]+".attachedFk", channelBox=True, lock=True)
        cmds.addAttr(self.main_controllers[1], shortName="attachedFKVis", niceName="Attached FK Visibility", attributeType="bool", keyable=True)

        clamped_distance = cmds.createNode("distanceBetween", name=f"{self.side}_neckToHeadClamped_DIB", ss=True)
        real_distance = cmds.createNode("distanceBetween", name=f"{self.side}_neckToHeadReal_DIB", ss=True)
        cmds.connectAttr(f"{self.main_controllers[0]}.worldMatrix[0]", f"{real_distance}.inMatrix1")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{real_distance}.inMatrix2")

        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{clamped_distance}.inMatrix1")
        cmds.connectAttr(f"{self.guides[-1]}.worldMatrix[0]", f"{clamped_distance}.inMatrix2")

        neck_toHead_blendTwo = cmds.createNode("blendTwoAttr", name=f"{self.side}_neckToHeadDistance_B2A", ss=True)
        cmds.connectAttr(f"{clamped_distance}.distance", f"{neck_toHead_blendTwo}.input[0]")
        cmds.connectAttr(f"{real_distance}.distance", f"{neck_toHead_blendTwo}.input[1]")
        cmds.connectAttr(f"{self.main_controllers[1]}.stretch", f"{neck_toHead_blendTwo}.attributesBlender")

        neck_world_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_neckWM_AIM", ss=True)
        cmds.connectAttr(f"{self.main_controllers[0]}.worldMatrix[0]", f"{neck_world_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{neck_world_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{neck_world_matrix}.primaryInputAxis", *self.primary_aim_vector, type="double3")
        cmds.setAttr(f"{neck_world_matrix}.secondaryInputAxis", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{neck_world_matrix}.secondaryTargetVector", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{neck_world_matrix}.secondaryMode", 2)
        head_translate_offset = cmds.createNode("fourByFourMatrix", name=f"{self.side}_headTranslateOffset_FBM", ss=True)
        cmds.connectAttr(f"{neck_toHead_blendTwo}.output", f"{head_translate_offset}.in31")

        head_end_pos = cmds.createNode("multMatrix", name=f"{self.side}_headEndPos_MMT", ss=True)
        cmds.connectAttr(f"{head_translate_offset}.output", f"{head_end_pos}.matrixIn[0]")
        cmds.connectAttr(f"{neck_world_matrix}.outputMatrix", f"{head_end_pos}.matrixIn[1]")

        head_wm = cmds.createNode("blendMatrix", name=f"{self.side}_headEnd_WM_BMX", ss=True)
        cmds.connectAttr(f"{head_end_pos}.matrixSum", f"{head_wm}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{head_wm}.target[0].targetMatrix")
        cmds.setAttr(f"{head_wm}.target[0].translateWeight", 0)

        cvs = [f"{neck_world_matrix}.outputMatrix", f"{head_wm}.outputMatrix"]

        t_values = []
        for i in range(self.num_joints):
            t = i / (float(self.num_joints) - 1)
            t_values.append(t)
        t_values.pop(-1)


        self.old_joints = de_boors_002.de_boor_ribbon(aim_axis=self.primary_aim, up_axis=self.secondary_aim, cvs=cvs, num_joints=self.num_joints-1, name=f"{self.side}_neck", parent=self.skinning_trn, custom_parm=t_values)

        self.input_connections = []
        for joint in self.old_joints:
            input_connection = cmds.listConnections(f"{joint}.offsetParentMatrix", source=True, destination=False, plugs=True)[0]
            self.input_connections.append(input_connection)

        self.input_connections.append(f"{head_wm}.outputMatrix")

        self.attached_fk()


    def attached_fk(self):
        """
        Creates the attached FK controllers for the neck module, including sub-neck controllers and joints.

        Args:
            self: Instance of the SpineModule class.
        Returns:
            list: A list of sub-neck joint names created for the attached FK system.
        """
        
        ctls_sub_neck = []
        sub_neck_ctl_trn = cmds.createNode("transform", n=f"{self.side}_subNeckControllers_GRP", parent=self.controllers_trn, ss=True)
        cmds.setAttr(f"{sub_neck_ctl_trn}.inheritsTransform", 0)
        cmds.connectAttr(f"{self.main_controllers[1]}.attachedFKVis", f"{sub_neck_ctl_trn}.visibility")

        for i, joint in enumerate(self.input_connections):
            name = joint.split(".")[0].split("_")[1]
            if "Scale" in name or "End" in name:
                name = name.replace("Scale", "").replace("End", "")

            ctl, controller_grp = controller_creator(
                name=f"{self.side}_{name}AttachedFk",
                suffixes=["GRP", "ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
                parent=ctls_sub_neck[-1] if ctls_sub_neck else sub_neck_ctl_trn
            )

            if i == 0:
                cmds.connectAttr(f"{joint}", f"{controller_grp[0]}.offsetParentMatrix")

            else:
                mmt = cmds.createNode("multMatrix", n=f"{self.side}neckSubAttachedFk0{i+1}_MMT")

                inverse = cmds.createNode("inverseMatrix", n=f"{self.side}_neckSubAttachedFk0{i+1}_IMX")
                cmds.connectAttr(f"{self.input_connections[i-1]}", f"{inverse}.inputMatrix")
                cmds.connectAttr(f"{joint}", f"{mmt}.matrixIn[0]")
                cmds.connectAttr(f"{inverse}.outputMatrix", f"{mmt}.matrixIn[1]")
                cmds.connectAttr(f"{mmt}.matrixSum", f"{controller_grp[0]}.offsetParentMatrix")

                for attr in ["translateX","translateY","translateZ", "rotateX", "rotateY", "rotateZ"]:
                    cmds.setAttr(f"{controller_grp[0]}.{attr}", 0)

            ctls_sub_neck.append(ctl)

        cmds.delete(self.old_joints)

        for ctl in ctls_sub_neck:
            name = ctl.replace("AttachedFk_CTL", "_JNT")
            joint_skin = cmds.createNode("joint", n=name, parent=self.skinning_trn, ss=True)
            cmds.connectAttr(f"{ctl}.worldMatrix[0]", f"{joint_skin}.offsetParentMatrix")


class BipedNeck(NeckModule):
    """
    Class to create a biped neck module in a Maya rigging setup.
    This module extends the NeckModule class and handles
    the creation of a biped neck joint chain, controllers, and various systems such as stretch, reverse, offset, squash, and volume preservation.
    """
    def __init__(self):
        """
        Initializes the BipedNeck class, setting up paths and data exporters.
        
        Args:
            self: Instance of the BipedNeck class.
        """
        super().__init__()

    def make(self, guide_name):
        self.primary_aim = "y"
        self.secondary_aim = "z"
        self.num_joints = 5
        self.bendy = False

        super().make(guide_name)

class QuadrupedNeck(NeckModule):
    """
    Class to create a quadruped neck module in a Maya rigging setup.
    This module extends the NeckModule class and handles
    the creation of a quadruped neck joint chain, controllers, and various systems such as stretch, reverse, offset, squash, and volume preservation.
    """
    def __init__(self):
        """
        Initializes the BipedNeck class, setting up paths and data exporters.
        
        Args:
            self: Instance of the BipedNeck class.
        """
        super().__init__()

    def make(self, guide_name):
        self.primary_aim = "z"
        self.secondary_aim = "y"
        self.num_joints = 5
        self.bendy = True

        super().make(guide_name)



cmds.file(new=True, force=True)

core.DataManager.set_guide_data("D:/git/maya/biped_autorig/guides/moana_01.guides")
core.DataManager.set_ctls_data("D:/git/maya/biped_autorig/curves/moana_01.ctls")

basic_structure.create_basic_structure(asset_name="moana_02")
a = BipedNeck().make("C_neck_GUIDE")
