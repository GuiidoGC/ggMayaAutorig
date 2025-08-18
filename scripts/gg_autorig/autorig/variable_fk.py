#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export

# Dev only imports
from gg_autorig.utils.guides import guides_manager

reload(guides_manager)


class VariableFkModule(object):

    def __init__(self):

        self.data_exporter = data_export.DataExport()

        self.modules_grp = self.data_exporter.get_data("basic_structure", "modules_GRP")
        self.skel_grp = self.data_exporter.get_data("basic_structure", "skel_GRP")
        self.masterWalk_ctl = self.data_exporter.get_data("basic_structure", "masterWalk_CTL")
        self.guides_grp = self.data_exporter.get_data("basic_structure", "guides_GRP")


    def make(self, guide_name):

        self.guide_name = guide_name
        self.side = guide_name.split("_")[0]

        """
        Create a limb rig with controllers and constraints.
        This function sets up the basic structure for a limb, including controllers and constraints.
        """      

        self.guides = guide_import(self.guide_name, all_descendents=True, path=None)

        if cmds.attributeQuery("moduleName", node=self.guides[0], exists=True):
            self.enum_str = cmds.attributeQuery("moduleName", node=self.guides[0], listEnum=True)[0]

            
        if cmds.attributeQuery("prefix", node=self.guides[0], exists=True):
            self.prefix = cmds.attributeQuery("prefix", node=self.guides[0], listEnum=True)[0]

        self.individual_module_grp = cmds.createNode("transform", name=f"{self.side}_{self.prefix}VariableFkModule_GRP", parent=self.modules_grp, ss=True)
        self.individual_controllers_grp = cmds.createNode("transform", name=f"{self.side}_{self.prefix}VariableFkControllers_GRP", parent=self.masterWalk_ctl, ss=True)
        self.skinnging_grp = cmds.createNode("transform", name=f"{self.side}_{self.prefix}VariableFkSkinningJoints_GRP", parent=self.skel_grp, ss=True)

        cmds.addAttr(self.skinnging_grp, longName="moduleName", attributeType="enum", enumName=self.enum_str, keyable=False)
        cmds.addAttr(self.skinnging_grp, longName="prefix", attributeType="enum", enumName=self.prefix, keyable=False)

        self.create_surface()

        self.data_exporter.append_data(
            f"{self.side}_{self.prefix}VariableFkModule",
            {
                "skinning_transform": self.skinnging_grp,
                "main_ctl": self.main_ctl,
                "end_main_ctl" : self.ctls[-1],
            }
        )

    def create_surface(self):
        """
        Create a surface for the variable FK module.
        This function creates a surface based on the guides provided for the variable FK module.
        """

        guide_positions = [cmds.xform(g, q=True, ws=True, t=True) for g in self.guides]

        curve = cmds.curve(d=3, p=guide_positions, name=f"{self.side}_{self.prefix}_variableFK_crv")
        cmds.delete(curve, ch=True)

        cmds.xform(curve, ws=True, r=True, t=[1, 0, 0])

        curve_dup = cmds.duplicate(curve, name=f"{self.side}_{self.prefix}_variableFK_crv_dup")[0]

        cmds.xform(curve_dup, ws=True, r=True, t=[-2, 0, 0])

        surface = cmds.loft(curve, curve_dup, name=f"{self.side}_{self.prefix}variableFK_NSF", ch=False, u=True, c=False, ar=True)[0]
        cmds.delete(curve, curve_dup)
        cmds.rebuildSurface(surface, rpo=1, rt=0, end=1, kr=0, kcp=1, kc=0, su=10, du=3, sv=10, dv=3, tol=0.01, fr=0, dir=2)
        cmds.parent(surface, self.individual_module_grp)

        self.end_joints = []

        joint_transform = cmds.createNode("transform", name=f"{self.side}_{self.prefix}VariableFkJoints_GRP", parent=self.individual_module_grp, ss=True)

        self.main_ctl, self.main_ctl_grp = controller_creator(
                    name=f"{self.side}_{self.prefix}VariableFkMain",
                    suffixes=["GRP", "ANM"],
                    lock=["visibility"],
                    ro=True,
                )
        
        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{self.main_ctl_grp[0]}.offsetParentMatrix")
        cmds.parent(self.main_ctl_grp[0], self.individual_controllers_grp)
        cmds.connectAttr(f"{self.main_ctl}.worldMatrix[0]", f"{joint_transform}.offsetParentMatrix")
        
        decompose = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.prefix}VariableFkScale_DM")
        cmds.connectAttr(f"{self.main_ctl}.worldMatrix[0]", f"{decompose}.inputMatrix")

        for i, guide in enumerate(self.guides):
            cmds.select(clear=True)
            joint = cmds.joint(name=f"{self.side}_{self.prefix}VariableFk{i+1:02d}_JNT")
            cmds.addAttr(joint, longName='Jnt_Pos', attributeType='double', defaultValue=i / float(len(self.guides) - 1), keyable=True)
            cmds.setAttr(joint + ".radius", 7)

            cmds.xform(joint, ws=True, t=cmds.xform(guide, q=True, ws=True, t=True))
            cmds.parent(joint, self.end_joints[-1] if self.end_joints else joint_transform)
            self.end_joints.append(joint)

        skinCluster = cmds.skinCluster(
            self.end_joints,
            surface,
            tsb=True,
            mi=3,
            dr=0.5
        )

        for i, joint in enumerate(self.end_joints[:-1]):
            if i == 0:
                cmds.skinPercent(skinCluster[0], f"{surface}.cv[0][{i}]", transformValue=(joint, 1))
                cmds.skinPercent(skinCluster[0], f"{surface}.cv[1][{i}]", transformValue=(joint, 1))
                cmds.skinPercent(skinCluster[0], f"{surface}.cv[2][{i}]", transformValue=(joint, 1))
                cmds.skinPercent(skinCluster[0], f"{surface}.cv[3][{i}]", transformValue=(joint, 1))    

            cmds.skinPercent(skinCluster[0], f"{surface}.cv[0][{i+1}]", transformValue=(joint, 1))
            cmds.skinPercent(skinCluster[0], f"{surface}.cv[1][{i+1}]", transformValue=(joint, 1))
            cmds.skinPercent(skinCluster[0], f"{surface}.cv[2][{i+1}]", transformValue=(joint, 1))
            cmds.skinPercent(skinCluster[0], f"{surface}.cv[3][{i+1}]", transformValue=(joint, 1))


        self.ctls = []
        self.ctls_grp = []

        variable_ctl_trn = cmds.createNode("transform", name=f"{self.side}_{self.prefix}VariableFkCtls_GRP", parent=self.individual_controllers_grp, ss=True)
        cmds.setAttr(f"{variable_ctl_trn}.inheritsTransform", 0)


        for i in range(3):

            ctl, ctl_grp = controller_creator(
                    name=f"{self.side}_{self.prefix}VariableFk{i+1:02d}",
                    suffixes=["GRP", "ANM"],
                    lock=["tx","tz","ty", "visibility"],
                    ro=True,
                )


            cmds.parent(ctl_grp[0], variable_ctl_trn)

            cmds.addAttr(ctl, shortName="extraAttr", niceName="Extra Attributes  ———", enumName="———",attributeType="enum", keyable=True)
            cmds.setAttr(ctl+".extraAttr", channelBox=True, lock=True)
            cmds.addAttr(ctl, shortName="pos", niceName="Position", defaultValue=0, minValue=(-0.5 * i), maxValue=(1 - 0.5 * i), keyable=True)
            cmds.addAttr(ctl, shortName="falloff", niceName="Falloff", minValue=0.0001,defaultValue=0.2, keyable=True)
            cmds.addAttr(ctl, shortName="ctl_pos", niceName="Ctl Position", minValue=0.0001,defaultValue=1, keyable=False)

            float_math = cmds.createNode("floatMath", name=f"{self.side}_{self.prefix}VariableFk{i+1:02d}_FLM")
            cmds.connectAttr(f"{ctl}.pos", f"{float_math}.floatA")
            cmds.setAttr(f"{float_math}.operation", 0)  
            cmds.setAttr(f"{float_math}.floatB", 0.5 * i)
            cmds.connectAttr(f"{float_math}.outFloat", f"{ctl}.ctl_pos")

            pointOnSurface = cmds.createNode("pointOnSurfaceInfo", name=f"{self.side}_{self.prefix}VariableFk{i+1:02d}_POSI")
            cmds.connectAttr(f"{surface}.worldSpace[0]", f"{pointOnSurface}.inputSurface")
            cmds.setAttr(f"{pointOnSurface}.parameterU", 0.5)
            cmds.connectAttr(f"{ctl}.ctl_pos", f"{pointOnSurface}.parameterV")


            pointOnSurface_Aim = cmds.createNode("pointOnSurfaceInfo", name=f"{self.side}_{self.prefix}VariableFkAim{i+1:02d}_POSI")
            cmds.connectAttr(f"{surface}.worldSpace[0]", f"{pointOnSurface_Aim}.inputSurface")
            cmds.setAttr(f"{pointOnSurface_Aim}.parameterU", 0.5)
            condition = cmds.createNode("condition", name=f"{self.side}_{self.prefix}VariableFkAim{i+1:02d}_CON")
            cmds.connectAttr(f"{ctl}.ctl_pos", f"{condition}.firstTerm")
            cmds.setAttr(f"{condition}.secondTerm", 1)
            cmds.setAttr(f"{condition}.operation", 0)
            cmds.setAttr(f"{condition}.colorIfTrue", -0.01, 1, 0, type="double3")
            cmds.setAttr(f"{condition}.colorIfFalse", 0.01, -1, 0, type="double3")
            float_math = cmds.createNode("floatMath", name=f"{self.side}_{self.prefix}VariableFkAim{i+1:02d}_FLM")
            cmds.connectAttr(f"{condition}.outColorR", f"{float_math}.floatA")
            cmds.setAttr(f"{float_math}.operation", 0)
            cmds.connectAttr(f"{ctl}.ctl_pos", f"{float_math}.floatB")
            cmds.connectAttr(f"{float_math}.outFloat", f"{pointOnSurface_Aim}.parameterV")

            aim_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_{self.prefix}VariableFkAim{i+1:02d}_AMX")
            cmds.setAttr(f"{aim_matrix}.primaryInputAxis", 0, 0, 0, type="double3")

            compose = cmds.createNode("composeMatrix", name=f"{self.side}_{self.prefix}VariableFk{i+1:02d}_CM")
            cmds.connectAttr(f"{pointOnSurface}.position", f"{compose}.inputTranslate")
            cmds.connectAttr(f"{compose}.outputMatrix", f"{aim_matrix}.inputMatrix")


            compose_aim = cmds.createNode("composeMatrix", name=f"{self.side}_{self.prefix}VariableFkAim{i+1:02d}_CM")
            cmds.connectAttr(f"{pointOnSurface_Aim}.position", f"{compose_aim}.inputTranslate")
            cmds.connectAttr(f"{compose_aim}.outputMatrix", f"{aim_matrix}.primaryTargetMatrix")
            cmds.connectAttr(f"{condition}.outColorG", f"{aim_matrix}.primaryInputAxisY")

            cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")


            self.ctls.append(ctl)
            self.ctls_grp.append(ctl_grp)

        self.connect_joint_behavior()

    def connect_joint_behavior(self):
        """
        Build utility nodes that connect controller rotations to joint rotations with falloff-based blending.
        """

        plusminusaverage_nodes = []
        multiply_divide_nodes = []
        add_Falloff_nodes = []
        check_if_out_pos_nodes = []
        check_if_out_neg_nodes = []
        get_range_nodes = []
        sub_Falloff_nodes = []
        pow_nodes = []
        abs_nodes = []
        percentage_nodes = []
        rev_percentage_nodes = []


        for k, joint in enumerate(self.end_joints):
            plusminusaverage_node = cmds.createNode("plusMinusAverage", name = f"{self.side}_{self.prefix}VariableFk{k+1:02d}_PMA")
            plusminusaverage_nodes.append(plusminusaverage_node)

            for i, ctl in enumerate(self.ctls):


                add_Falloff_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}AddFalloff{i+1}_FML")
                add_Falloff_nodes.append(add_Falloff_node)

                check_if_out_pos_node = cmds.createNode("condition", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}CheckIfOutPos{i+1}_CON")
                check_if_out_pos_nodes.append(check_if_out_pos_node)

                check_if_out_neg_node = cmds.createNode("condition", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}CheckIfOutNeg{i+1}_CON")
                check_if_out_neg_nodes.append(check_if_out_neg_node)

                multiply_divide_node = cmds.createNode("multiplyDivide", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}MultiplyDivide{i+1}_MDV")
                multiply_divide_nodes.append(multiply_divide_node)

                get_range_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}GetRange{i+1:02d}_FLM")
                get_range_nodes.append(get_range_node)

                sub_Falloff_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}SubFalloff{i+1:02d}_FML")
                sub_Falloff_nodes.append(sub_Falloff_node)

                pow_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}POW{i+1:02d}_FML")
                pow_nodes.append(pow_node)

                abs_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}ABS{i+1:02d}_FML")
                abs_nodes.append(abs_node)

                percentage_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}Percentage{i+1:02d}_FLM")
                percentage_nodes.append(percentage_node)

                rev_percentage_node = cmds.createNode("floatMath", name= f"{self.side}_{self.prefix}VariableFk{k+1:02d}RevPercentage{i+1:02d}_FLM")
                rev_percentage_nodes.append(rev_percentage_node)

                cmds.setAttr(add_Falloff_node + ".operation", 0) 
                cmds.connectAttr(f"{ctl}.ctl_pos", add_Falloff_node + ".floatA")
                cmds.connectAttr(f"{ctl}.falloff", add_Falloff_node + ".floatB")

                cmds.setAttr(check_if_out_pos_node + ".operation", 3)
                cmds.connectAttr(f"{ctl}.rotateX", check_if_out_pos_node + ".colorIfTrueR")
                cmds.connectAttr(f"{ctl}.rotateY", check_if_out_pos_node + ".colorIfTrueG")
                cmds.connectAttr(f"{ctl}.rotateZ", check_if_out_pos_node + ".colorIfTrueB")
                cmds.setAttr(check_if_out_pos_node + ".colorIfFalseR", 0)
                cmds.setAttr(check_if_out_pos_node + ".colorIfFalseG", 0)
                cmds.setAttr(check_if_out_pos_node + ".colorIfFalseB", 0)
                cmds.connectAttr(add_Falloff_node + ".outFloat", check_if_out_pos_node + ".firstTerm")

                cmds.setAttr(check_if_out_neg_node + ".operation", 4) 
                cmds.connectAttr(check_if_out_pos_node + ".outColor", check_if_out_neg_node + ".colorIfTrue")
                cmds.setAttr(check_if_out_neg_node + ".colorIfFalseR", 0)
                cmds.setAttr(check_if_out_neg_node + ".colorIfFalseG", 0)
                cmds.setAttr(check_if_out_neg_node + ".colorIfFalseB", 0)
                cmds.connectAttr(f"{joint}.Jnt_Pos", check_if_out_pos_node + ".secondTerm")
                cmds.connectAttr(f"{joint}.Jnt_Pos", check_if_out_neg_node + ".secondTerm")
                cmds.connectAttr(check_if_out_neg_node + ".outColor", multiply_divide_node + ".input2")

                cmds.setAttr(sub_Falloff_node + ".operation", 1)
                cmds.connectAttr(f"{ctl}.ctl_pos", sub_Falloff_node + ".floatA")
                cmds.connectAttr(f"{ctl}.falloff", sub_Falloff_node + ".floatB")
                cmds.connectAttr(sub_Falloff_node + ".outFloat", check_if_out_neg_node + ".firstTerm")

                cmds.setAttr(get_range_node + ".operation", 1) 

                cmds.connectAttr(f"{ctl}.ctl_pos", get_range_node + ".floatA")
                cmds.connectAttr(f"{joint}.Jnt_Pos", get_range_node + ".floatB")

                cmds.setAttr(pow_node + ".operation", 6)
                cmds.setAttr(pow_node + ".floatB", 2)


                cmds.setAttr(abs_node + ".operation", 6)
                cmds.setAttr(abs_node + ".floatB", 0.5)
                cmds.connectAttr(pow_node + ".outFloat", abs_node + ".floatA")



                cmds.connectAttr(get_range_node + ".outFloat", pow_node + ".floatA")

                cmds.setAttr(percentage_node + ".operation", 3) 


                cmds.connectAttr(abs_node + ".outFloat", percentage_node + ".floatA")

                cmds.connectAttr(f"{ctl}.falloff", percentage_node + ".floatB")
                cmds.setAttr(rev_percentage_node + ".operation", 1) 


                cmds.setAttr(rev_percentage_node + ".floatA", 1)

                cmds.connectAttr(rev_percentage_node + ".outFloat", multiply_divide_node + ".input1X")
                cmds.connectAttr(rev_percentage_node + ".outFloat", multiply_divide_node + ".input1Y")
                cmds.connectAttr(rev_percentage_node + ".outFloat", multiply_divide_node + ".input1Z")
                cmds.connectAttr(percentage_node + ".outFloat", rev_percentage_node + ".floatB")

                cmds.connectAttr(f"{multiply_divide_node}.output", f"{plusminusaverage_node}.input3D[{i + 1}]")




        for i, joint in enumerate(self.end_joints):
           
            cormd_node = cmds.createNode("multiplyDivide", name=f"{self.side}_{self.prefix}Correct_{i + 1:02d}_MDV")

            cmds.connectAttr(plusminusaverage_nodes[i] + ".output3Dx", cormd_node + ".input1X")
            cmds.connectAttr(plusminusaverage_nodes[i] + ".output3Dy", cormd_node + ".input1Y")
            cmds.connectAttr(plusminusaverage_nodes[i] + ".output3Dz", cormd_node + ".input1Z")
            cmds.connectAttr(f"{cormd_node}.outputX", f"{joint}.rotateX")
            cmds.connectAttr(f"{cormd_node}.outputY", f"{joint}.rotateY")
            cmds.connectAttr(f"{cormd_node}.outputZ", f"{joint}.rotateZ")

            cmds.setAttr(f"{cormd_node}.input2X", 1)
            cmds.setAttr(f"{cormd_node}.input2Z", 1)

            cmds.select(clear=True)
            joint_end = cmds.joint(name=f"{self.side}_{self.prefix}{i+1:02d}_JNT")
            cmds.parent(joint_end, self.skinnging_grp)
            cmds.connectAttr(f"{joint}.worldMatrix[0]", f"{joint_end}.offsetParentMatrix")

        

