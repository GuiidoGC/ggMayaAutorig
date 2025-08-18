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

        self.module_trn = cmds.createNode("transform", name=f"C_neckModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"C_neckControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.skinning_trn = cmds.createNode("transform", name=f"C_neckSkinning_GRP", ss=True, p=self.skel_grp)

        pick_matrix = cmds.createNode("pickMatrix", name="C_neckPickMatrix_PMX", ss=True)
        cmds.connectAttr(f"{self.masterWalk_ctl}.worldMatrix[0]", f"{pick_matrix}.inputMatrix")
        cmds.connectAttr(f"{pick_matrix}.outputMatrix", f"{self.module_trn}.offsetParentMatrix")

        self.create_chain()

        self.data_exporter.append_data(f"C_neckModule", 
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

        aim_matrix = cmds.createNode("aimMatrix", name="C_neck01Guide_AMX", ss=True)
        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{aim_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{aim_matrix}.primaryTargetMatrix")
        cmds.setAttr(f"{aim_matrix}.primaryInputAxis", 0, 0, 1, type="double3")

        blend_matrix = cmds.createNode("blendMatrix", name="C_headGuide_BMX", ss=True)
        cmds.connectAttr(f"{self.guides[1]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].translateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].rotateWeight", 0)

   
        self.main_controllers = []
        self.main_controllers_grp = []

        self.guide_matrix = [aim_matrix, blend_matrix]
        name = ["neck", "head"]

        for i, matrix in enumerate(self.guide_matrix ):
            ctl, ctl_grp = controller_creator(
                name=f"C_{name[i]}",
                suffixes=["GRP", "OFF","ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.parent(ctl_grp[0], self.controllers_trn)


            cmds.connectAttr(f"{matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")



            self.main_controllers.append(ctl)
            self.main_controllers_grp.append(ctl_grp)

        num_joints = 5

        self.distance_between = cmds.createNode("distanceBetween", name="C_neckDistance_BTW", ss=True)

        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{self.distance_between}.inMatrix1")
        cmds.connectAttr(f"{self.guides[-1]}.worldMatrix[0]", f"{self.distance_between}.inMatrix2")

        self.twist_division = cmds.createNode("floatMath", name="C_neckTwistDivision_FLM", ss=True)
        cmds.setAttr(f"{self.twist_division}.operation", 3) 
        cmds.connectAttr(f"{self.distance_between}.distance", f"{self.twist_division}.floatA")
        cmds.setAttr(f"{self.twist_division}.floatB", num_joints - 1)

        self.main_chain = []
        for i in range(num_joints):
            cmds.select(clear=True)
            joint = cmds.joint(name=f"C_neck0{i+1}_JNT")
            cmds.parent(joint, self.main_chain[-1] if self.main_chain else self.module_trn)
            cmds.setAttr(f"{joint}.tz", cmds.getAttr(f"{self.twist_division}.outFloat"))

            self.main_chain.append(joint)

        point1 = cmds.xform(self.main_controllers[0], query=True, worldSpace=True, translation=True)
        point2 = cmds.xform(self.main_controllers[1], query=True, worldSpace=True, translation=True)
        self.curve = cmds.curve(d=1, p=(point1,point2), n="C_neck_CRV")
        cmds.delete(self.curve, constructionHistory = True)

        self.ik_handle = cmds.ikHandle(sj=self.main_chain[0], ee=self.main_chain[-1], sol="ikSplineSolver", n="C_neck_HDL", createCurve=False, curve=self.curve,parentCurve=False)[0]
        cmds.parent(self.ik_handle, self.curve, self.module_trn)

        self.parentName = cmds.listRelatives(self.curve, shapes=True)[0]
        self.parentName = cmds.rename(self.parentName, f"{self.curve}Shape")

        cmds.setAttr(f"{self.curve}.inheritsTransform", 0)

        self.controllers_dcp = []

        for i, ctl in enumerate([self.main_controllers[0],self.main_controllers[1]]):
            dcp = cmds.createNode("decomposeMatrix", name=ctl.replace("_CTL", "_DCP"), ss=True)
            cmds.connectAttr(f"{ctl}.worldMatrix[0]", f"{dcp}.inputMatrix")
            cmds.connectAttr(f"{dcp}.outputTranslate", f"{self.curve}.controlPoints[{i}]")
            self.controllers_dcp.append(dcp)

        cmds.setAttr(f"{self.ik_handle}.dTwistControlEnable", 1) 
        cmds.setAttr(f"{self.ik_handle}.dWorldUpType", 4)
        cmds.setAttr(f"{self.ik_handle}.dForwardAxis", 4)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpAxis", 0)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpVectorX", 0)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpVectorY", 1)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpVectorZ", 0)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpVectorEndX", 0)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpVectorEndY", 1)
        cmds.setAttr(f"{self.ik_handle}.dWorldUpVectorEndZ", 0)
        cmds.connectAttr(f"{self.main_controllers[0]}.worldMatrix[0]", f"{self.ik_handle}.dWorldUpMatrix")
        cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{self.ik_handle}.dWorldUpMatrixEnd")

        self.stretch_system()

    def stretch_system(self):
        """
        Creates the stretch system for the neck module, including attributes and nodes for stretch and squash functionality.
        
        Args:
            self: Instance of the SpineModule class.
        """
           
        cmds.addAttr(self.main_controllers[1], shortName="STRETCH", niceName="Stretch ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.main_controllers[1]+".STRETCH", channelBox=True, lock=True)
        cmds.addAttr(self.main_controllers[1], shortName="stretch", niceName="Stretch", maxValue=1, minValue=0,defaultValue=0, keyable=True)
        cmds.addAttr(self.main_controllers[1], shortName="stretchMin", niceName="Stretch Min", maxValue=1, minValue=0.001,defaultValue=0.8, keyable=True)
        cmds.addAttr(self.main_controllers[1], shortName="stretchMax", niceName="Stretch Max", minValue=1,defaultValue=1.2, keyable=True)
        cmds.addAttr(self.main_controllers[1], shortName="offset", niceName="Offset", maxValue=1, minValue=0,defaultValue=0, keyable=True)

        cmds.addAttr(self.main_controllers[1], shortName="SQUASH", niceName="Squash ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.main_controllers[1]+".SQUASH", channelBox=True, lock=True)
        cmds.addAttr(self.main_controllers[1], shortName="volumePreservation", niceName="Volume Preservation", maxValue=1, minValue=0,defaultValue=1, keyable=True)
        cmds.addAttr(self.main_controllers[1], shortName="falloff", niceName="Falloff", maxValue=1, minValue=0,defaultValue=0, keyable=True)
        cmds.addAttr(self.main_controllers[1], shortName="maxPos", niceName="Max Pos", maxValue=1, minValue=0.001,defaultValue=0.5, keyable=True)

        cmds.addAttr(self.main_controllers[1], shortName="attachedFk", niceName="Fk ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.main_controllers[1]+".attachedFk", channelBox=True, lock=True)
        cmds.addAttr(self.main_controllers[1], shortName="attachedFKVis", niceName="Attached FK Visibility", attributeType="bool", keyable=True)


        nodes_to_create = {
            "C_neck_CIN": ("curveInfo", None), #0
            "C_neckStretchFactor_FLM": ("floatMath", 3), #1
            "C_neckStretchFactor_CLM": ("clamp", None), #2
            "C_neckInitialArcLegth_FLM": ("floatMath", 2), #3
            "C_neckBaseStretch_FLC": ("floatConstant", None), #4
            "C_neckStretch_BTA": ("blendTwoAttr", None), # 5
            "C_neckStretchValue_FLM": ("floatMath", 2),# 6
        }

        created_nodes = []
        for node_name, (node_type, operation) in nodes_to_create.items():
            node = cmds.createNode(node_type, name=node_name)
            created_nodes.append(node)
            if operation is not None:
                cmds.setAttr(f'{node}.operation', operation)

        cmds.connectAttr(created_nodes[0] + ".arcLength", created_nodes[1]+".floatA")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[2]+".inputR")
        cmds.connectAttr(created_nodes[3] + ".outFloat", created_nodes[1]+".floatB")
        cmds.connectAttr(created_nodes[2] + ".outputR", created_nodes[5]+".input[1]")
        cmds.connectAttr(created_nodes[4] + ".outFloat", created_nodes[5]+".input[0]")
        cmds.connectAttr(created_nodes[5] + ".output", created_nodes[6]+".floatA")
        cmds.setAttr(created_nodes[4]+".inFloat", 1)
        cmds.connectAttr(f"{self.main_controllers[1]}.stretch", created_nodes[5]+".attributesBlender")
        cmds.connectAttr(f"{self.main_controllers[1]}.stretchMax", created_nodes[2]+".maxR")
        cmds.connectAttr(f"{self.main_controllers[1]}.stretchMin", created_nodes[2]+".minR")
        cmds.connectAttr(f"{self.parentName}.worldSpace[0]", created_nodes[0]+".inputCurve")
        cmds.connectAttr(f"{self.distance_between}.distance", f"{created_nodes[3]}.floatB")
        cmds.connectAttr(f"{self.masterWalk_ctl}.globalScale", created_nodes[3]+".floatA")
        cmds.connectAttr(f"{self.twist_division}.outFloat", f"{created_nodes[6]}.floatB")
        for i, joint in enumerate(self.main_chain[1:]):
            if i == len(self.main_chain)-2:
                cmds.connectAttr(f"{self.controllers_dcp[1]}.outputRotate", f"{joint}.rotate")
            cmds.connectAttr(created_nodes[6]+".outFloat", f"{joint}.translateZ")

        self.stretch_float_math = created_nodes[6]

        self.reverse_system()

    def reverse_system(self):
        """
        Creates the reverse system for the neck module, including a reversed curve and an IK spline handle for the reversed chain.

        Args:
            self: Instance of the SpineModule class.
        """

        reversed_curve = cmds.reverseCurve(self.curve, name="C_neckReversed_CRV",  ch=True, rpo=False)
        cmds.setAttr(f"{reversed_curve[0]}.inheritsTransform", 0)
        cmds.parent(reversed_curve[0], self.module_trn ) 
        reversed_joints = cmds.duplicate(self.main_chain[0], renameChildren=True)

        self.reverse_chain = []
        for i, joint in enumerate(reversed(reversed_joints)):
            if "effector" in joint:
                reversed_joints.remove(joint)
                cmds.delete(joint)
                
            else:
                renamed_joint = cmds.rename(joint, f"C_neckReversed0{i}_JNT")
                if i != 5:
                    cmds.parent(renamed_joint, world=True)
                self.reverse_chain.append(renamed_joint) 
        for i, joint in enumerate(self.reverse_chain):
            if i != 0:
                cmds.parent(joint, self.reverse_chain[i-1])


        cmds.parent(self.reverse_chain[0], self.module_trn)
        hdl = cmds.ikHandle(sj=self.reverse_chain[0], ee=self.reverse_chain[-1], sol="ikSplineSolver", n="C_neckReversed_HDL", parentCurve=False, curve=reversed_curve[0], createCurve=False) # Create an IK spline handle
        cmds.parent(hdl[0], self.module_trn) 


        negate_flm = cmds.createNode("floatMath", n="C_neckNegateStretchValue_FLM")
        cmds.setAttr("C_neckNegateStretchValue_FLM.operation", 2)
        cmds.setAttr("C_neckNegateStretchValue_FLM.floatB", -1)
        cmds.connectAttr(self.stretch_float_math+".outFloat", f"{negate_flm}.floatA")

        for joint in self.reverse_chain[1:]:
            cmds.connectAttr(negate_flm+".outFloat", f"{joint}.translateY")

        self.offset_system()

    def offset_system(self):
        """
        Creates the offset system for the neck module, including nodes for decomposing matrices, nearest point on curve, float constants, and blend two attributes.

        Args:
            self: Instance of the SpineModule class.
        """
        nodes_to_create = {
            "C_neckReversed05_DCM": ("decomposeMatrix", None),
            "C_neckOffset_NPC": ("nearestPointOnCurve", None),
            "C_neckOffsetInitialValue_FLC": ("floatConstant", None),
            "C_neckOffset_BTA": ("blendTwoAttr", None),
        }

        created_nodes = []
        for node_name, (node_type, operation) in nodes_to_create.items():
            node = cmds.createNode(node_type, name=node_name)
            created_nodes.append(node)
            if operation is not None:
                cmds.setAttr(f'{node}.operation', operation)

        cmds.connectAttr(created_nodes[0] + ".outputTranslate", created_nodes[1]+".inPosition")
        cmds.connectAttr(created_nodes[1] + ".parameter", created_nodes[3]+".input[1]")
        cmds.connectAttr(created_nodes[2] + ".outFloat", created_nodes[3]+".input[0]")
        cmds.connectAttr(f"{self.main_controllers[1]}.offset", created_nodes[3]+".attributesBlender")
        cmds.connectAttr(f"{self.reverse_chain[-1]}.worldMatrix[0]", created_nodes[0]+".inputMatrix")
        cmds.connectAttr(f"{self.curve}.worldSpace[0]", created_nodes[1]+".inputCurve")
        cmds.connectAttr(f"{created_nodes[3]}.output", self.ik_handle +".offset")
        cmds.setAttr(created_nodes[2]+".inFloat", 0)

        self.squash_system()

    def squash_system(self):
        """
        Creates the squash system for the neck module, including a transform node for neck settings, attributes for stretch and squash, and a curve for squash deformation.

        Args:
            self: Instance of the SpineModule class.
        """

        translations = []

        self.neck_settings_trn = cmds.createNode("transform", n="C_neckSettings_TRN", parent=self.module_trn)
        for attribute in ["translateX","translateY","translateZ","rotateX","rotateY","rotateZ","scaleX","scaleY","scaleZ","visibility"]:
            cmds.setAttr(f"{self.neck_settings_trn}.{attribute}", lock=True, keyable=False, channelBox=False)

        cmds.addAttr(self.neck_settings_trn, shortName="maxStretchLength", niceName="Max Stretch Length", minValue=1,defaultValue=2, keyable=True)
        cmds.addAttr(self.neck_settings_trn, shortName="minStretchLength", niceName="Min Stretch Length", maxValue=1, minValue=0.001,defaultValue=0.5, keyable=True)
        cmds.addAttr(self.neck_settings_trn, shortName="maxStretchEffect", niceName="Max Stretch Effect", minValue=1,defaultValue=2, keyable=True)
        cmds.addAttr(self.neck_settings_trn, shortName="minStretchEffect", niceName="Min Stretch Effect", maxValue=1, minValue=0.001,defaultValue=0.5, keyable=True)
        
        cmds.addAttr(self.neck_settings_trn, shortName="VolumeSep", niceName="Volume_____", enumName="_____",attributeType="enum", keyable=True)
        cmds.setAttr(self.neck_settings_trn+".VolumeSep", channelBox=True, lock=True)
        
        for i in range(len(self.main_chain)):
            if i == 0:
                default_value = 0.05
            if i == len(self.main_chain)-1:
                default_value = 0.95
            else:
                default_value = (1/(len(self.main_chain)-1))*i
            cmds.addAttr(self.neck_settings_trn, shortName=f"neck0{i+1}SquashPercentage", niceName="Spine01 Squash Percentage", maxValue=1, minValue=0,defaultValue=default_value, keyable=True)

        for joint in self.main_chain:
            translation = cmds.xform(f"{joint}", query=True, worldSpace=True, translation=True)
            translations.append(translation)
        squash_curve = cmds.curve(p=translations, d=1, n="C_neckSquash_CRV")
        cmds.setAttr(squash_curve+".inheritsTransform", 0)
        cmds.parent(squash_curve, self.module_trn)
        

        for i, joint in enumerate(self.main_chain):
            dcm = cmds.createNode("decomposeMatrix", n=f"C_{joint}Squash_DCM")
            cmds.connectAttr(f"{joint}.worldMatrix[0]", f"{dcm}.inputMatrix")
            cmds.connectAttr(f"{dcm}.outputTranslate", f"{squash_curve}.controlPoints[{i}]")

        nodes_to_create = {
            "C_neckSquash_CIN": ("curveInfo", None),
            "C_neckSquashBaseLength_FLM": ("floatMath", 2),
            "C_neckSquashFactor_FLM": ("floatMath", 3),
        }

        created_nodes = []
        for node_name, (node_type, operation) in nodes_to_create.items():
            node = cmds.createNode(node_type, name=node_name)
            created_nodes.append(node)
            if operation is not None:   
                cmds.setAttr(f'{node}.operation', operation)

        cmds.connectAttr(f"{squash_curve}.worldSpace[0]", created_nodes[0]+".inputCurve")
        cmds.connectAttr(created_nodes[0] + ".arcLength", created_nodes[2]+".floatA")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[2]+".floatB") 
        cmds.connectAttr(f"{self.masterWalk_ctl}.globalScale", created_nodes[1]+".floatA") 
        cmds.setAttr(created_nodes[1]+".floatB", cmds.getAttr(created_nodes[0]+".arcLength"))

        self.squash_factor_fml = created_nodes[2]

        self.volume_preservation_system()

    def attached_fk(self):
        """
        Creates the attached FK controllers for the neck module, including sub-neck controllers and joints.

        Args:
            self: Instance of the SpineModule class.
        Returns:
            list: A list of sub-neck joint names created for the attached FK system.
        """
        
        main_neck_joint = []
        for joint in self.main_chain:
            if "effector" in joint:
                    self.main_chain.remove(joint)
            else:
                main_neck_joint.append(f"{joint}")

        ctls_sub_neck = []
        sub_neck_ctl_trn = cmds.createNode("transform", n="C_subNeckControllers_GRP", parent=self.masterWalk_ctl)
        cmds.setAttr(f"{sub_neck_ctl_trn}.inheritsTransform", 0)
        cmds.connectAttr(f"{self.main_controllers[1]}.attachedFKVis", f"{sub_neck_ctl_trn}.visibility")

        for i, joint in enumerate(main_neck_joint):
            
            ctl, controller_grp = controller_creator(
                name=f"C_neckSubAttachedFk0{i+1}",
                suffixes=["GRP", "ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
                parent=ctls_sub_neck[-1] if ctls_sub_neck else sub_neck_ctl_trn
            )
                
            if i == 0:
                cmds.connectAttr(f"{joint}.worldMatrix[0]", f"{controller_grp[0]}.offsetParentMatrix")

            elif i == len(main_neck_joint)-1:
                blendMatrix = cmds.createNode("blendMatrix", n=f"C_neckSubAttachedFk0{i+1}_BMX")
                mmt = cmds.createNode("multMatrix", n=f"C_neckSubAttachedFk0{i+1}_MMT")

                cmds.connectAttr(f"{joint}.worldMatrix[0]", f"{blendMatrix}.inputMatrix")
                cmds.connectAttr(f"{self.main_controllers[1]}.worldMatrix[0]", f"{blendMatrix}.target[0].targetMatrix")
                cmds.setAttr(f"{blendMatrix}.target[0].translateWeight", 0)
                cmds.setAttr(f"{blendMatrix}.target[0].shearWeight", 0)



                cmds.connectAttr(f"{main_neck_joint[i-1]}.worldInverseMatrix[0]", f"{mmt}.matrixIn[1]")
                cmds.connectAttr(f"{blendMatrix}.outputMatrix", f"{mmt}.matrixIn[0]")
                cmds.connectAttr(f"{mmt}.matrixSum", f"{controller_grp[0]}.offsetParentMatrix")

                for attr in ["translateX","translateY","translateZ", "rotateX", "rotateY", "rotateZ"]:
                    cmds.setAttr(f"{controller_grp[0]}.{attr}", 0)



            else:
                mmt = cmds.createNode("multMatrix", n=f"C_neckSubAttachedFk0{i+1}_MMT")

                cmds.connectAttr(f"{joint}.worldMatrix[0]", f"{mmt}.matrixIn[0]")
                cmds.connectAttr(f"{main_neck_joint[i-1]}.worldInverseMatrix[0]", f"{mmt}.matrixIn[1]")
                cmds.connectAttr(f"{mmt}.matrixSum", f"{controller_grp[0]}.offsetParentMatrix")

                for attr in ["translateX","translateY","translateZ", "rotateX", "rotateY", "rotateZ"]:
                    cmds.setAttr(f"{controller_grp[0]}.{attr}", 0)

            ctls_sub_neck.append(ctl)

        self.sub_neck_joints = []
        for i, joint in enumerate(main_neck_joint):
            cmds.select(clear=True)
            new_joint = cmds.joint(joint, name=f"C_subNeckFk0{i+1}_JNT")
            cmds.setAttr(f"{new_joint}.inheritsTransform", 0)

            cmds.parent(new_joint, self.skinning_trn)

            cmds.connectAttr(f"{ctls_sub_neck[i]}.worldMatrix[0]", f"{new_joint}.offsetParentMatrix")
            for attr in ["translateX","translateY","translateZ"]:
                cmds.setAttr(f"{new_joint}.{attr}", 0)
            self.sub_neck_joints.append(new_joint)

        return self.sub_neck_joints

    def volume_preservation_system(self):
        """
        Creates the volume preservation system for the neck module, including remap value nodes, float math nodes, and connections to squash joints.

        Args:
            self: Instance of the SpineModule class.
        """
                
        squash_joints = self.attached_fk()
       
        nodes_to_create = {
            "C_neckVolumeLowBound_RMV": ("remapValue", None),# 0
            "C_neckVolumeHighBound_RMV": ("remapValue", None),# 1
            "C_neckVolumeLowBoundNegative_FLM": ("floatMath", 1),# 2
            "C_neckVolumeHighBoundNegative_FLM": ("floatMath", 1),# 3
            "C_neckVolumeSquashDelta_FLM": ("floatMath", 1), # 4
            "C_neckVolumeStretchDelta_FLM": ("floatMath", 1), # 5
        } 

        main_created_nodes = []
        for node_name, (node_type, operation) in nodes_to_create.items():
            node = cmds.createNode(node_type, name=node_name)
            main_created_nodes.append(node)
            if operation is not None:
                cmds.setAttr(f'{node}.operation', operation)
        values = [0.001, 0.999]
        for i in range(0,2):
            cmds.connectAttr(f"{self.main_controllers[1]}.falloff", f"{main_created_nodes[i]}.inputValue")
            cmds.connectAttr(f"{self.main_controllers[1]}.maxPos", f"{main_created_nodes[i]}.outputMin")
            cmds.setAttr(f"{main_created_nodes[i]}.outputMax", values[i])
            cmds.connectAttr(f"{main_created_nodes[i]}.outValue", f"{main_created_nodes[i+2]}.floatB")

        cmds.setAttr(f"{main_created_nodes[2]}.floatA", 0)
        cmds.setAttr(f"{main_created_nodes[3]}.floatA", 2)
        cmds.setAttr(f"{main_created_nodes[4]}.floatB", 1)
        cmds.setAttr(f"{main_created_nodes[5]}.floatA", 1)
        cmds.connectAttr(f"{self.neck_settings_trn}.maxStretchEffect", f"{main_created_nodes[4]}.floatA")
        cmds.connectAttr(f"{self.neck_settings_trn}.minStretchEffect", f"{main_created_nodes[5]}.floatB")

        for i, joint in enumerate(squash_joints):
            nodes_to_create = {
                f"C_neckVolumeSquashFactor0{i+1}_FLM": ("floatMath", 2), # 0
                f"C_neckVolumeStretchFactor0{i+1}_FLM": ("floatMath", 2), # 1
                f"C_neckVolumeStretchFullValue0{i+1}_FLM": ("floatMath", 1), # 2
                f"C_neckVolumeSquashFullValue0{i+1}_FLM": ("floatMath", 0), # 3
                f"C_neckVolume0{i+1}_RMV": ("remapValue", None), # 4
                f"C_neckVolumeFactor0{i+1}_RMV": ("remapValue", None), # 5
            }

            created_nodes = []
            for node_name, (node_type, operation) in nodes_to_create.items():
                node = cmds.createNode(node_type, name=node_name)
                created_nodes.append(node)
                if operation is not None:
                    cmds.setAttr(f'{node}.operation', operation)

            cmds.connectAttr(f"{self.neck_settings_trn}.neck0{i+1}SquashPercentage", f"{created_nodes[5]}.inputValue")
            cmds.connectAttr(f"{main_created_nodes[2]}.outFloat", f"{created_nodes[5]}.value[0].value_Position")
            cmds.connectAttr(f"{main_created_nodes[0]}.outValue", f"{created_nodes[5]}.value[1].value_Position")
            cmds.connectAttr(f"{main_created_nodes[1]}.outValue", f"{created_nodes[5]}.value[2].value_Position")
            cmds.connectAttr(f"{main_created_nodes[3]}.outFloat", f"{created_nodes[5]}.value[3].value_Position")


            cmds.connectAttr(created_nodes[0] + ".outFloat", created_nodes[3]+".floatA")
            cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[2]+".floatB")
            cmds.connectAttr(created_nodes[2] + ".outFloat", created_nodes[4]+".value[2].value_FloatValue")
            cmds.connectAttr(created_nodes[3] + ".outFloat", created_nodes[4]+".value[0].value_FloatValue")
            cmds.connectAttr(self.squash_factor_fml + ".outFloat", created_nodes[4]+".inputValue")
            cmds.setAttr(f"{created_nodes[3]}.floatB", 1)
            cmds.setAttr(f"{created_nodes[2]}.floatA", 1)

            cmds.connectAttr(f"{main_created_nodes[4]}.outFloat", created_nodes[0]+".floatA")
            cmds.connectAttr(f"{main_created_nodes[5]}.outFloat", created_nodes[1]+".floatA")
            cmds.connectAttr(f"{created_nodes[5]}.outValue", created_nodes[0]+".floatB")
            cmds.connectAttr(f"{created_nodes[5]}.outValue", created_nodes[1]+".floatB")

            cmds.connectAttr(f"{self.neck_settings_trn}.maxStretchLength", f"{created_nodes[4]}.value[2].value_Position")
            cmds.connectAttr(f"{self.neck_settings_trn}.minStretchLength", f"{created_nodes[4]}.value[0].value_Position")   

            floatConstant = cmds.createNode("floatConstant", name=f"C_neckVolume0{i+1}_FLC", ss=True)
            blendTwoAttr = cmds.createNode("blendTwoAttr", name=f"C_neckVolume0{i+1}_BTA", ss=True)
            cmds.connectAttr(f"{created_nodes[4]}.outValue", f"{blendTwoAttr}.input[1]")
            cmds.connectAttr(f"{floatConstant}.outFloat", f"{blendTwoAttr}.input[0]")
            cmds.connectAttr(f"{self.main_controllers[1]}.volumePreservation", f"{blendTwoAttr}.attributesBlender")

            cmds.connectAttr(f"{blendTwoAttr}.output",f"{joint}.scaleX")   
            cmds.connectAttr(f"{blendTwoAttr}.output",f"{joint}.scaleZ")   


            values = [-1, 1, 1, -1]
            for i in range(0,4):
                cmds.setAttr(f"{created_nodes[5]}.value[{i}].value_Interp", 2)
                cmds.setAttr(f"{created_nodes[5]}.value[{i}].value_FloatValue", values[i])
