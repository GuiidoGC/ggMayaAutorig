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
from gg_autorig.utils import de_boor_core_002
from gg_autorig.utils.space_switch import fk_switch

reload(data_export)

AXIS_VECTOR = {'x': (1, 0, 0), '-x': (-1, 0, 0), 'y': (0, 1, 0), '-y': (0, -1, 0), 'z': (0, 0, 1), '-z': (0, 0, -1)}


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

        self.primary_aim = "z"
        self.primary_aim_vector = AXIS_VECTOR[self.primary_aim]
        self.secondary_aim = "y"
        self.secondary_aim_vector = AXIS_VECTOR[self.secondary_aim]

        self.side = self.guide_name.split("_")[0]

        self.module_trn = cmds.createNode("transform", name=f"{self.side}_spineModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"{self.side}_spineControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.skinning_trn = cmds.createNode("transform", name=f"{self.side}_spineSkinning_GRP", ss=True, p=self.skel_grp)

        pick_matrix = cmds.createNode("pickMatrix", name=f"{self.side}_spinePickMatrix_PMX", ss=True)
        cmds.connectAttr(f"{self.masterWalk_ctl}.worldMatrix[0]", f"{pick_matrix}.inputMatrix")
        cmds.connectAttr(f"{pick_matrix}.outputMatrix", f"{self.module_trn}.offsetParentMatrix")

        self.create_chain()

        # self.data_exporter.append_data(f"{self.side}_spineModule", 
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


        aim_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_spine01Guide_AMX", ss=True)
        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{aim_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{aim_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{aim_matrix}.primaryInputAxis", *self.primary_aim_vector, type="double3")

        blend_matrix = cmds.createNode("blendMatrix", name=f"{self.side}_spine03Guide_BMX", ss=True)
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].translateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)

        blend_matrix02 = cmds.createNode("blendMatrix", name=f"{self.side}_spine02Guide_BMX", ss=True)
        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{blend_matrix02}.inputMatrix")
        cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{blend_matrix02}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix02}.target[0].weight", 0.5)
        cmds.setAttr(f"{blend_matrix02}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix02}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrix02}.target[0].shearWeight", 0)


        self.main_controllers = []
        self.main_controllers_grp = []

        self.guide_matrix = [aim_matrix, blend_matrix02, blend_matrix]

        for i, matrix in enumerate(self.guide_matrix ):
            name = f"Tan0{i}" if i == 1 else f"0{i+1}"
            ctl, ctl_grp = controller_creator(
                name=f"{self.side}_spine{name}",
                suffixes=["GRP", "ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.parent(ctl_grp[0], self.main_controllers[0] if i == 2 else self.controllers_trn)

            if i == 2:
                offset_multMatrix = cmds.createNode("multMatrix", name=f"{self.side}_spineOffset{name}_MMX", ss=True)
                inverse_matrix = cmds.createNode("inverseMatrix", name=f"{self.side}_spineOffset{name}_IMX", ss=True)
                cmds.connectAttr(f"{matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[0]")

                cmds.connectAttr(f"{self.guide_matrix[0]}.outputMatrix", f"{inverse_matrix}.inputMatrix")

                cmds.connectAttr(f"{inverse_matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[1]")
        

                cmds.connectAttr(f"{offset_multMatrix}.matrixSum", f"{ctl_grp[0]}.offsetParentMatrix")

                for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                    cmds.setAttr(f"{ctl_grp[0]}.{attr}", 0)

            elif i == 1:
                parent_matrix = cmds.createNode("parentMatrix", name=f"{self.side}_spine{name}_PMX", ss=True)
                cmds.connectAttr(f"{matrix}.outputMatrix", f"{parent_matrix}.inputMatrix")
                cmds.connectAttr(f"{parent_matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")


            else:
                cmds.connectAttr(f"{matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")



            self.main_controllers.append(ctl)
            self.main_controllers_grp.append(ctl_grp)

        fk_switch(target= self.main_controllers[1], sources= [self.main_controllers[2], self.main_controllers[0]])
        cmds.setAttr(f"{self.main_controllers[1]}.RotateValue", lock=True, keyable=False)

        self.localChest_ctl, localChest_grp = controller_creator(
            name=f"{self.side}_localChest",
            suffixes=["GRP", "ANM"],
            lock=["scaleX", "scaleY", "scaleZ", "visibility"],
            ro=True,
            parent=self.controllers_trn
        )

        # blend_matrix_localChest = cmds.createNode("blendMatrix", name=f"{self.side}_localChest_BMX", ss=True)
        # cmds.connectAttr(f"{self.main_controllers[-1]}.worldMatrix[0]", f"{blend_matrix_localChest}.inputMatrix")
        # cmds.connectAttr(f"{self.main_chain[-1]}.worldMatrix[0]", f"{blend_matrix_localChest}.target[0].targetMatrix")
        # cmds.setAttr(f"{blend_matrix_localChest}.target[0].shearWeight", 0)
        # cmds.setAttr(f"{blend_matrix_localChest}.target[0].rotateWeight", 0)
        # cmds.setAttr(f"{blend_matrix_localChest}.target[0].scaleWeight", 0)
        # cmds.connectAttr(f"{blend_matrix_localChest}.outputMatrix", f"{localChest_grp[0]}.offsetParentMatrix")
        # cmds.connectAttr(f"{self.localChest_ctl}.worldMatrix[0]", f"{self.chest_fix}.offsetParentMatrix")

        self.local_hip_guide = guide_import(f"{self.side}_localHip_GUIDE", all_descendents=True, path=None)

        self.localHip_ctl, localHip_grp = controller_creator(
            name=f"{self.side}_localHip",
            suffixes=["GRP", "ANM"],
            lock=["scaleX", "scaleY", "scaleZ", "visibility"],
            ro=True,
            parent=self.controllers_trn
        )

        local_hip_joint = cmds.createNode("joint", n=f"{self.side}_localHip_JNT", p=self.skinning_trn, ss=True)
        cmds.connectAttr(f"{self.localHip_ctl}.worldMatrix[0]", f"{local_hip_joint}.offsetParentMatrix")
            
        self.body_ctl, body_grp = controller_creator(
            name=f"{self.side}_body",
            suffixes=["GRP", "ANM"],
            lock=["scaleX", "scaleY", "scaleZ", "visibility"],
            ro=True,
            parent=self.controllers_trn
        )

        for ctl in [localHip_grp[0], localChest_grp[0]]:
            cmds.setAttr(f"{ctl}.inheritsTransform", 0)

        cmds.connectAttr(f"{self.guide_matrix[0]}.outputMatrix", f"{body_grp[0]}.offsetParentMatrix")

        cmds.parent(self.main_controllers_grp[0][0], self.body_ctl)

        movable_ctl = controller_creator(f"{self.side}_movablePivot", 
                                                          suffixes=[], 
                                                          lock=["scaleX", "scaleY", "scaleZ", "visibility"], 
                                                          ro=True, 
                                                          parent=self.body_ctl)
        
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
            cmds.setAttr(f"{movable_ctl}.{attr}", 0)
        

        cmds.connectAttr(f"{movable_ctl}.translate", f"{self.body_ctl}.rotatePivot") 
        cmds.connectAttr(f"{movable_ctl}.translate", f"{self.body_ctl}.scalePivot") 

        dummy_body = cmds.createNode("transform", n=f"{self.side}_dummyBody_TRN", p=self.body_ctl) 

        parent_matrix = cmds.createNode("parentMatrix", name=f"{self.side}_hipPosition_PMX", ss=True)
        cmds.connectAttr(f"{self.local_hip_guide[0]}.worldMatrix[0]", f"{parent_matrix}.inputMatrix")
        cmds.connectAttr(f"{dummy_body}.worldMatrix[0]", f"{parent_matrix}.target[0].targetMatrix")

        child_dag = om.MSelectionList().add(self.local_hip_guide[0]).getDagPath(0)
        parent_dag = om.MSelectionList().add(dummy_body).getDagPath(0)

        child_world_matrix = child_dag.inclusiveMatrix()
        parent_world_matrix = parent_dag.inclusiveMatrix()
        
        offset_matrix = child_world_matrix * parent_world_matrix.inverse()

        cmds.setAttr(f"{parent_matrix}.target[0].offsetMatrix", offset_matrix, type="matrix")
        cmds.connectAttr(f"{parent_matrix}.outputMatrix", f"{localHip_grp[0]}.offsetParentMatrix")


        cmds.addAttr(self.body_ctl, shortName="STRETCH", niceName="Stretch ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.body_ctl+".STRETCH", channelBox=True, lock=True)
        cmds.addAttr(self.body_ctl, shortName="stretch", niceName="Stretch", maxValue=1, minValue=0,defaultValue=0, keyable=True)

        cmds.addAttr(self.body_ctl, shortName="attachedFk", niceName="Fk ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.body_ctl+".attachedFk", channelBox=True, lock=True)
        cmds.addAttr(self.body_ctl, shortName="attachedFKVis", niceName="Attached FK Visibility", attributeType="bool", keyable=True)

        print(self.main_controllers)

        clamped_distance = cmds.createNode("distanceBetween", name=f"{self.side}_spineToTan01_DIB", ss=True)
        real_distance = cmds.createNode("distanceBetween", name=f"{self.side}_spineToTan01_DIB", ss=True)
        cmds.connectAttr(f"{self.main_controllers[0]}.worldMatrix[0]", f"{real_distance}.inMatrix1")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{real_distance}.inMatrix2")

        cmds.connectAttr(f"{self.guide_matrix[0]}.outputMatrix", f"{clamped_distance}.inMatrix1")
        cmds.connectAttr(f"{self.guide_matrix[1]}.outputMatrix", f"{clamped_distance}.inMatrix2")

        spine_to_tan01_blendTwo = cmds.createNode("blendTwoAttr", name=f"{self.side}_spineToTan01_B2A", ss=True)
        cmds.connectAttr(f"{clamped_distance}.distance", f"{spine_to_tan01_blendTwo}.input[0]")
        cmds.connectAttr(f"{real_distance}.distance", f"{spine_to_tan01_blendTwo}.input[1]")
        cmds.connectAttr(f"{self.body_ctl}.stretch", f"{spine_to_tan01_blendTwo}.attributesBlender")

        spine01_world_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_spine01WM_AIM", ss=True)
        cmds.connectAttr(f"{self.main_controllers[0]}.worldMatrix[0]", f"{spine01_world_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{spine01_world_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{spine01_world_matrix}.primaryInputAxis", *self.primary_aim_vector, type="double3")
        cmds.setAttr(f"{spine01_world_matrix}.secondaryInputAxis", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{spine01_world_matrix}.secondaryTargetVector", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{spine01_world_matrix}.secondaryMode", 2)
        tan01_translate_offset = cmds.createNode("fourByFourMatrix", name=f"{self.side}_tan01TranslateOffset_FBM", ss=True)
        cmds.connectAttr(f"{spine_to_tan01_blendTwo}.output", f"{tan01_translate_offset}.in32")

        tan01_end_pos = cmds.createNode("multMatrix", name=f"{self.side}_tan01EndPos_MMT", ss=True)
        cmds.connectAttr(f"{tan01_translate_offset}.output", f"{tan01_end_pos}.matrixIn[0]")
        cmds.connectAttr(f"{spine01_world_matrix}.outputMatrix", f"{tan01_end_pos}.matrixIn[1]")

        tan01_wm_no_rot = cmds.createNode("blendMatrix", name=f"{self.side}_tan01EndWMNoRot_BMX", ss=True)
        cmds.connectAttr(f"{tan01_end_pos}.matrixSum", f"{tan01_wm_no_rot}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{tan01_wm_no_rot}.target[0].targetMatrix")
        cmds.setAttr(f"{tan01_wm_no_rot}.target[0].translateWeight", 0)

        clamped_distance_tan_spine = cmds.createNode("distanceBetween", name=f"{self.side}_tan01ToSpine_DIB", ss=True)
        real_distance_tan_spine = cmds.createNode("distanceBetween", name=f"{self.side}_tan01ToSpine_DIB", ss=True)
        cmds.connectAttr(f"{tan01_wm_no_rot}.outputMatrix", f"{real_distance_tan_spine}.inMatrix1")
        cmds.connectAttr(f"{self.main_controllers[2]}.worldMatrix[0]", f"{real_distance_tan_spine}.inMatrix2")

        cmds.connectAttr(f"{self.guide_matrix[1]}.outputMatrix", f"{clamped_distance_tan_spine}.inMatrix1")
        cmds.connectAttr(f"{self.guide_matrix[2]}.outputMatrix", f"{clamped_distance_tan_spine}.inMatrix2")

        tan01_to_spine01_blendTwo = cmds.createNode("blendTwoAttr", name=f"{self.side}_tan01ToSpine01_B2A", ss=True)
        cmds.connectAttr(f"{clamped_distance_tan_spine}.distance", f"{tan01_to_spine01_blendTwo}.input[0]")
        cmds.connectAttr(f"{real_distance_tan_spine}.distance", f"{tan01_to_spine01_blendTwo}.input[1]")
        cmds.connectAttr(f"{self.body_ctl}.stretch", f"{tan01_to_spine01_blendTwo}.attributesBlender")

        tan01_world_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_tan01WM_AIM", ss=True)
        cmds.connectAttr(f"{tan01_wm_no_rot}.outputMatrix", f"{tan01_world_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[2]}.worldMatrix[0]", f"{tan01_world_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{tan01_world_matrix}.primaryInputAxis", *self.primary_aim_vector, type="double3")
        cmds.setAttr(f"{tan01_world_matrix}.secondaryInputAxis", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{tan01_world_matrix}.secondaryTargetVector", *self.secondary_aim_vector, type="double3")
        cmds.setAttr(f"{tan01_world_matrix}.secondaryMode", 2)
        spine02_translate_offset = cmds.createNode("fourByFourMatrix", name=f"{self.side}_spine02TranslateOffset_FBM", ss=True)
        cmds.connectAttr(f"{tan01_to_spine01_blendTwo}.output", f"{spine02_translate_offset}.in32")

        spine02_end_pos = cmds.createNode("multMatrix", name=f"{self.side}_spine02EndPos_MMT", ss=True)
        cmds.connectAttr(f"{spine02_translate_offset}.output", f"{spine02_end_pos}.matrixIn[0]")
        cmds.connectAttr(f"{tan01_world_matrix}.outputMatrix", f"{spine02_end_pos}.matrixIn[1]")

        spine_wm = cmds.createNode("blendMatrix", name=f"{self.side}_spine02WM_BMX", ss=True)
        cmds.connectAttr(f"{spine02_end_pos}.matrixSum", f"{spine_wm}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{spine_wm}.target[0].targetMatrix")
        cmds.setAttr(f"{spine_wm}.target[0].translateWeight", 0)

        cvs = [f"{spine01_world_matrix}.outputMatrix", f"{tan01_world_matrix}.outputMatrix", f"{spine_wm}.outputMatrix"]

        self.num_joints = 5

        t_values = []
        for i in range(self.num_joints):
            t = i / (float(self.num_joints) - 1)
            t_values.append(t)

        self.old_joints = de_boor_core_002.de_boor_ribbon(aim_axis=self.primary_aim, up_axis=self.secondary_aim, cvs=cvs, num_joints=self.num_joints, name=f"{self.side}_spine", parent=self.skinning_trn, custom_parm=t_values)

        self.input_connections = []
        for joint in self.old_joints:
            input_connection = cmds.listConnections(f"{joint}.offsetParentMatrix", source=True, destination=False, plugs=True)[0]
            self.input_connections.append(input_connection)

        local_chest_blend_matrix = cmds.createNode("blendMatrix", name=f"{self.side}_localChest_BMX", ss=True)
        cmds.connectAttr(f"{self.input_connections[-1]}", f"{local_chest_blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.main_controllers[-1]}.worldMatrix[0]", f"{local_chest_blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{local_chest_blend_matrix}.target[0].translateWeight", 0)
        cmds.connectAttr(f"{local_chest_blend_matrix}.outputMatrix", f"{localChest_grp[0]}.offsetParentMatrix")

        self.input_connections[-1] = f"{self.localChest_ctl}.worldMatrix[0]"

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
        cmds.connectAttr(f"{self.body_ctl}.attachedFKVis", f"{sub_neck_ctl_trn}.visibility")

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

cmds.file(new=True, force=True)

core.DataManager.set_guide_data("H:/ggMayaAutorig/guides/elephant_04.guides")
core.DataManager.set_ctls_data("H:/ggMayaAutorig/curves/body_template_01.ctls")

basic_structure.create_basic_structure(asset_name="elephant_04")
a = SpineModule().make("C_spine01_GUIDE")
