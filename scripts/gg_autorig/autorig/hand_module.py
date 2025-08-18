#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export
from gg_autorig.utils import space_switch

reload(data_export)
reload(space_switch)

class HandModule():
    """
    Class to create a hand module in a Maya rigging setup.
    This module handles the creation of hand joints, controllers, and various systems such as stretch, reverse, offset, squash, and volume preservation.
    """
    def __init__(self):
        """
        Initializes the HandModule class, setting up paths and data exporters.

        Args:
            self: Instance of the HandModule class.
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
        self.side = guide_name.split("_")[0] 

        if self.side == "L":
            self.value_mult = 1
        elif self.side == "R":
            self.value_mult = -1

        self.module_trn = cmds.createNode("transform", name=f"{self.side}_handModule_GRP", ss=True, parent=self.modules_grp)
        self.controllers_trn = cmds.createNode("transform", name=f"{self.side}_handControllers_GRP", ss=True, parent=self.masterWalk_ctl)
        self.ik_controllers_trn = cmds.createNode("transform", name=f"{self.side}_handIkControllers_GRP", ss=True, parent=self.controllers_trn)
        self.fk_controllers_trn = cmds.createNode("transform", name=f"{self.side}_handFkControllers_GRP", ss=True, parent=self.controllers_trn)
        self.skinning_trn = cmds.createNode("transform", name=f"{self.side}_handSkinning_GRP", ss=True, p=self.skel_grp)

        self.create_chain()

        self.data_exporter.append_data(f"{self.side}_HandModule", 
                                    {"skinning_transform": self.skinning_trn,
                                     "hand_controllers": self.controllers_trn,
                                     "main_ctl" : self.controllers_trn,
                                    }
                                  )


    def create_chain(self):
        """
        Creates the spine joint chain by importing guides and parenting the first joint to the module transform.

        Args:
            self: Instance of the SpineModule class.
        """
        
        self.guides = guide_import(self.guide_name, all_descendents=True, path=None)

        zero_transform = cmds.createNode("transform", name=f"{self.side}_handZero_TRN", ss=True)
        cmds.connectAttr(zero_transform + ".worldMatrix[0]", self.controllers_trn + ".offsetParentMatrix")
        cmds.parent(zero_transform, self.module_trn)

        if cmds.attributeQuery("moduleName", node=self.guides[0], exists=True):
            self.enum_str = cmds.attributeQuery("moduleName", node=self.guides[0], listEnum=True)[0]
        cmds.addAttr(self.skinning_trn, longName="moduleName", attributeType="enum", enumName=self.enum_str, keyable=False)

        self.hand_attribute_ctl, self.hand_attribute_ctl_grp = controller_creator(
            name=self.guides[0].replace("_GUIDE", "Attributes"),
            suffixes=["GRP", "ANM"],
            lock=["tx","tz","ty","ry","scaleX", "scaleY", "scaleZ", "visibility"],
            ro=True,
        )
        cmds.parent(self.hand_attribute_ctl_grp[0], self.controllers_trn)

        hand_settings_blend_matrix = cmds.createNode("blendMatrix", name=f"{self.guides[0].replace('_GUIDE', '_BMX')}", ss=True)
        cmds.connectAttr(f"{self.guides[0]}.worldMatrix[0]", f"{hand_settings_blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{hand_settings_blend_matrix}.outputMatrix", f"{self.hand_attribute_ctl_grp[0]}.offsetParentMatrix")

        cmds.addAttr(self.hand_attribute_ctl, shortName="extraAttr", niceName="Extra Attributes  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_attribute_ctl+".extraAttr", channelBox=True, lock=True)
        cmds.addAttr(self.hand_attribute_ctl, shortName="hideFk", niceName="Hide FK Controllers", enumName="Hide:Show",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_attribute_ctl+".hideFk", channelBox=True)
        cmds.addAttr(self.hand_attribute_ctl, shortName="hideIk", niceName="Hide Ik Controllers", enumName="Hide:Show",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_attribute_ctl+".hideIk", channelBox=True)
        cmds.addAttr(self.hand_attribute_ctl, shortName="handAttrs", niceName="Hand Attributes  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_attribute_ctl+".handAttrs", channelBox=True, lock=True)
        cmds.addAttr(self.hand_attribute_ctl, shortName="curl", niceName="Curl", defaultValue=0, minValue=-10, maxValue=10, keyable=True)
        # cmds.addAttr(self.hand_attribute_ctl, shortName="spread", niceName="Spread", defaultValue=0, minValue=-10, maxValue=10, keyable=True)
        # cmds.addAttr(self.hand_attribute_ctl, shortName="twist", niceName="Twist", defaultValue=0, minValue=-10, maxValue=10, keyable=True)
        cmds.addAttr(self.hand_attribute_ctl, shortName="fan", niceName="Fan", defaultValue=0, minValue=-10, maxValue=10, keyable=True)


        cmds.connectAttr(f"{self.hand_attribute_ctl}.hideFk", f"{self.fk_controllers_trn}.visibility")
        cmds.connectAttr(f"{self.hand_attribute_ctl}.hideIk", f"{self.ik_controllers_trn}.visibility")
        cmds.setAttr(f"{self.hand_attribute_ctl}.hideFk", 1)


        childs = cmds.listRelatives(self.guides[0], children=True)
        for index, child in enumerate(childs):
            guides_chain = [child]
            descendants = cmds.listRelatives(child, allDescendents=True) or []
            descendants.reverse()
            for desc in descendants:
                guides_chain.append(desc)

            joint_chain = []
            fk_ctls = []
            fk_ctls_grps = []

            guide_matrix = []

            meta_ctl, meta_ctl_grp = controller_creator(
                name=guides_chain[0].replace("_GUIDE", ""),
                suffixes=["GRP", "ANM"],
                lock=["tx","tz","ty","scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            if self.side == "L":
                self.primary_aim = (1, 0, 0)
                self.secondary_aim = (0, -1, 0)
            else:
                self.primary_aim = (-1, 0, 0)
                self.secondary_aim = (0, 1, 0)

            order = []
            for i, guides in enumerate(guides_chain):
                if i < 2:
                    input_node = guides_chain[i]
                    primary_target = guides_chain[i+1] if i+1 < len(guides_chain) else guides_chain[-1]
                    secondary_target = guides_chain[i+2] if i+2 < len(guides_chain) else guides_chain[-1]
                else:
                    input_node = guides_chain[i]
                    primary_target = guides_chain[i+1] if i+1 < len(guides_chain) else guides_chain[-1]
                    secondary_target = guides_chain[i-1] if i-1 >= 0 else guides_chain[0]
                order.append((input_node, primary_target, secondary_target))

            for i, guides in enumerate(guides_chain):
                if "metacarpalThumb" in guides  or "firstMetacarpal" in guides:
                    aim_matrix = cmds.createNode("blendMatrix", name=f"{guides.replace('_GUIDE', 'Guide_AMX')}", ss=True)
                    cmds.connectAttr(f"{guides}.worldMatrix[0]", f"{aim_matrix}.inputMatrix", force=True)

                else:
                    if i >= 3 or "End" in guides:

                        aim_matrix = cmds.createNode("blendMatrix", name=f"{guides.replace('_GUIDE', 'Guide_AMX')}", ss=True)
                        cmds.connectAttr(f"{guides}.worldMatrix[0]", f"{aim_matrix}.inputMatrix", force=True)
                        cmds.connectAttr(guide_matrix[-1], f"{aim_matrix}.target[0].targetMatrix", force=True)
                        cmds.setAttr(f"{aim_matrix}.target[0].scaleWeight", 0)
                        cmds.setAttr(f"{aim_matrix}.target[0].rotateWeight", 1)
                        cmds.setAttr(f"{aim_matrix}.target[0].shearWeight", 0)
                        cmds.setAttr(f"{aim_matrix}.target[0].translateWeight", 0)

                    else:

                        aim_matrix = cmds.createNode("aimMatrix", name=f"{guides.replace('_GUIDE', 'Guide_AMX')}", ss=True)
                        cmds.setAttr(aim_matrix + ".primaryInputAxis", *self.primary_aim, type="double3")
                        cmds.setAttr(aim_matrix + ".secondaryInputAxis", *self.secondary_aim, type="double3")
                        cmds.setAttr(aim_matrix + ".primaryMode", 1)
                        cmds.setAttr(aim_matrix + ".secondaryMode", 1)
                        cmds.connectAttr(order[i][0] + ".worldMatrix[0]", aim_matrix + ".inputMatrix")
                        cmds.connectAttr(order[i][1] + ".worldMatrix[0]", aim_matrix + ".primaryTargetMatrix")
                        cmds.connectAttr(order[i][2] + ".worldMatrix[0]", aim_matrix + ".secondaryTargetMatrix")

                guide_matrix.append(f"{aim_matrix}.outputMatrix")



            chain_length = guide_matrix[:-1] if len(guide_matrix) > 4 else guide_matrix

            half_chain_length = len(chain_length) // 2

            cmds.connectAttr(f"{guide_matrix[0]}", f"{hand_settings_blend_matrix}.target[{index}].targetMatrix")
            cmds.setAttr(f"{hand_settings_blend_matrix}.target[{index}].scaleWeight", 0)
            cmds.setAttr(f"{hand_settings_blend_matrix}.target[{index}].translateWeight", 0)
            cmds.setAttr(f"{hand_settings_blend_matrix}.target[{index}].shearWeight", 0)
            cmds.setAttr(f"{hand_settings_blend_matrix}.target[{index}].rotateWeight", 1)

            distances = []
            for i, guide in enumerate(chain_length):
                parent = (
                    self.skinning_trn if i == 0 else
                    self.module_trn if i == 1 else
                    joint_chain[-1]
                )
                replace_name = "Ik_JNT" if parent != self.skinning_trn else "_JNT"
                joint = cmds.createNode("joint", name=guide.replace("Guide_AMX.outputMatrix", replace_name), p=parent, ss=True)
                if not "End" in guide and i > 0:

                    ctl, ctl_grp = controller_creator(
                    name=guide.replace("Guide_AMX.outputMatrix", "Fk"),
                    suffixes=["GRP", "ANM"],
                    lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                    ro=True,
                    )

                    cmds.parent(ctl_grp[0], self.fk_controllers_trn if not fk_ctls else fk_ctls[-1])

                    fk_ctls.append(ctl)
                    fk_ctls_grps.append(ctl_grp)

                if i > 1:
                    if i + 1 <= len(guide_matrix):
                        pos1 = cmds.xform(guides_chain[i], q=True, ws=True, t=True)
                        pos2 = cmds.xform(guides_chain[i-1], q=True, ws=True, t=True)
                        distance = math.sqrt(
                            (pos2[0] - pos1[0]) ** 2 +
                            (pos2[1] - pos1[1]) ** 2 +
                            (pos2[2] - pos1[2]) ** 2
                        )
                        distance = distance * self.value_mult
                        cmds.setAttr(f"{joint}.tx", distance)
                        distances.append(distance)

                cmds.setAttr(f"{joint}.preferredAngle", 0, 0,-90, type="double3")
                joint_chain.append(joint)


            mult_matrix = cmds.createNode("multMatrix", name=f"{joint_chain[1].replace('_JNT', 'MMX')}", ss=True)
            inverse = cmds.createNode("inverseMatrix", name=f"{guides_chain[0].replace('_JNT', 'IMX')}", ss=True)
            cmds.connectAttr(f"{guide_matrix[0]}", f"{inverse}.inputMatrix")
            cmds.connectAttr(f"{guide_matrix[1]}", f"{mult_matrix}.matrixIn[0]")
            cmds.connectAttr(f"{inverse}.outputMatrix", f"{mult_matrix}.matrixIn[1]")
            cmds.connectAttr(f"{meta_ctl}.worldMatrix[0]", f"{mult_matrix}.matrixIn[2]")
            cmds.connectAttr(f"{mult_matrix}.matrixSum", f"{joint_chain[1]}.offsetParentMatrix")

            ik_ctl, ik_ctl_grp = controller_creator(
                name=guides_chain[-1].replace("End_GUIDE", "Ik"),
                suffixes=["GRP", "ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.connectAttr(f"{guide_matrix[-1]}", f"{ik_ctl_grp[0]}.offsetParentMatrix")

            pv_ctl, pv_ctl_grp = controller_creator(
                name=guides_chain[-1].replace("End_GUIDE", "Pv"),
                suffixes=["GRP", "ANM"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.connectAttr(f"{guide_matrix[2]}", f"{pv_ctl_grp[0]}.offsetParentMatrix")
            cmds.setAttr(f"{pv_ctl_grp[0]}.ty", distances[0])

            cmds.parent(ik_ctl_grp[0], pv_ctl_grp[0], self.ik_controllers_trn)
            cmds.parent(meta_ctl_grp[0], self.fk_controllers_trn)
            cmds.connectAttr(f"{meta_ctl}.worldMatrix[0]", f"{joint_chain[0]}.offsetParentMatrix")
            cmds.connectAttr(guide_matrix[0], f"{meta_ctl_grp[0]}.offsetParentMatrix")

            space_switch.fk_switch(target=ik_ctl, sources=[meta_ctl])



            ik_handle = cmds.ikHandle(
                name=f"{guides_chain[-1].replace('End_GUIDE', '_HDL')}",
                startJoint=joint_chain[1],
                endEffector=joint_chain[-1],
                solver="ikRPsolver"
            )[0]
            cmds.parent(ik_handle, self.module_trn)

            float_constant = cmds.createNode("floatConstant", name=f"{guides_chain[-1].replace('End_GUIDE', 'IkDummy_FloatConstant')}", ss=True)
            cmds.setAttr(f"{float_constant}.inFloat", 0)
            for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                cmds.connectAttr(f"{float_constant}.outFloat", f"{ik_handle}.{attr}")
            
            if len(guides_chain) == 5:
                dummy_trn = cmds.createNode("transform", name=f"{guides_chain[-1].replace('End_GUIDE', 'IkDummy_TRN')}", ss=True)
                cmds.parent(dummy_trn, self.module_trn)
                mult = cmds.createNode("multMatrix", name=f"{guides_chain[-1].replace('End_GUIDE', 'IkDummy_MMX')}", ss=True)
                cmds.connectAttr(f"{guide_matrix[-2]}", f"{mult}.matrixIn[0]")
                inverse = cmds.createNode("inverseMatrix", name=f"{guides_chain[-1].replace('End_GUIDE', 'IkDummy_INV')}", ss=True)
                cmds.connectAttr(f"{guide_matrix[-1]}", f"{inverse}.inputMatrix")
                cmds.connectAttr(f"{inverse}.outputMatrix", f"{mult}.matrixIn[1]")
                cmds.connectAttr(f"{ik_ctl}.worldMatrix[0]", f"{mult}.matrixIn[2]")
                cmds.connectAttr(f"{mult}.matrixSum", f"{dummy_trn}.offsetParentMatrix")
                cmds.connectAttr(f"{dummy_trn}.worldMatrix[0]", f"{ik_handle}.offsetParentMatrix")
            else:
                cmds.connectAttr(f"{ik_ctl}.worldMatrix[0]", f"{ik_handle}.offsetParentMatrix")

            cmds.poleVectorConstraint(pv_ctl, ik_handle)

            cmds.connectAttr(f"{joint_chain[1]}.worldMatrix[0]", f"{fk_ctls_grps[0][0]}.offsetParentMatrix")

            aim_matrix = cmds.createNode("aimMatrix", name=f"{joint_chain[2].replace('_JNT', 'Lock_AMX')}", ss=True)
            cmds.connectAttr(f"{joint_chain[2]}.worldMatrix[0]", f"{aim_matrix}.inputMatrix")
            cmds.connectAttr(f"{ik_ctl}.worldMatrix[0]", f"{aim_matrix}.primaryTargetMatrix")
            cmds.setAttr(aim_matrix + ".primaryInputAxis", *self.primary_aim, type="double3")

            mult_matrix = cmds.createNode("multMatrix", name=f"{joint_chain[2].replace('_JNT', 'LockOffset_MMX')}", ss=True)
            cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{mult_matrix}.matrixIn[0]")
            cmds.connectAttr(f"{joint_chain[1]}.worldInverseMatrix[0]", f"{mult_matrix}.matrixIn[1]")
            cmds.connectAttr(f"{mult_matrix}.matrixSum", f"{fk_ctls_grps[1][0]}.offsetParentMatrix")
            
            if len(fk_ctls) > 2:
                cmds.addAttr(ik_ctl, shortName="extraAttr", niceName="Extra Attributes  ———", enumName="———",attributeType="enum", keyable=True)
                cmds.setAttr(ik_ctl+".extraAttr", channelBox=True, lock=True)
                cmds.addAttr(ik_ctl, shortName="lockPhalange", niceName="Lock Phalange",defaultValue=1, minValue=0, maxValue=1, keyable=True)
                cmds.addAttr(ik_ctl, shortName="lastJointAim", niceName="Last Joint Aim",defaultValue=0, minValue=0, maxValue=1, keyable=True)

                rev = cmds.createNode("reverse", name=f"{ik_ctl}_lockPhalange_REV")
                cmds.connectAttr(f"{ik_ctl}.lockPhalange", f"{rev}.inputX")
                cmds.connectAttr(f"{rev}.outputX", f"{aim_matrix}.envelope")


                mult_matrix1 = cmds.createNode("multMatrix", name=f"{joint_chain[3].replace('_JNT', '01Lock_MMX')}", ss=True)
                mult_matrix2 = cmds.createNode("multMatrix", name=f"{joint_chain[3].replace('_JNT', '02Lock_MMX')}", ss=True)

                cmds.connectAttr(f"{joint_chain[3]}.worldMatrix[0]", f"{mult_matrix1}.matrixIn[0]")
                cmds.connectAttr(f"{joint_chain[2]}.worldInverseMatrix[0]", f"{mult_matrix1}.matrixIn[1]")
                cmds.connectAttr(f"{fk_ctls[1]}.worldMatrix[0]", f"{mult_matrix1}.matrixIn[2]")

                aim_matrix = cmds.createNode("aimMatrix", name=f"{joint_chain[3].replace('_JNT', 'Lock_AMX')}", ss=True)
                cmds.setAttr(aim_matrix + ".primaryInputAxis", *self.primary_aim, type="double3")
                cmds.connectAttr(f"{mult_matrix1}.matrixSum", f"{aim_matrix}.inputMatrix")
                cmds.connectAttr(f"{ik_ctl}.worldMatrix[0]", f"{aim_matrix}.primaryTargetMatrix")
                cmds.connectAttr(f"{aim_matrix}.outputMatrix", f"{mult_matrix2}.matrixIn[0]")
                cmds.connectAttr(f"{fk_ctls[1]}.worldInverseMatrix[0]", f"{mult_matrix2}.matrixIn[1]")
                cmds.connectAttr(f"{mult_matrix2}.matrixSum", f"{fk_ctls_grps[2][0]}.offsetParentMatrix")
 
                last_joint_aim_rev = cmds.createNode("reverse", name=f"{ik_ctl}_lastJointAim_REV")
                cmds.connectAttr(f"{ik_ctl}.lastJointAim", f"{last_joint_aim_rev}.inputX")
                cmds.connectAttr(f"{last_joint_aim_rev}.outputX", f"{aim_matrix}.envelope")

            cmds.setAttr(f"{fk_ctls_grps[0][0]}.inheritsTransform", 0)


            for i, ctl in enumerate(fk_ctls):
                end_joint = cmds.createNode("joint", name=ctl.replace("Fk_CTL", "_JNT"), p=self.skinning_trn, ss=True)
                cmds.connectAttr(f"{ctl}.worldMatrix[0]", f"{end_joint}.offsetParentMatrix")

                floatMath_curl = cmds.createNode("floatMath", name=f"{ctl.replace('_CTL', 'CurlRotation_FLM')}", ss=True)

                cmds.connectAttr(f"{self.hand_attribute_ctl}.curl", f"{floatMath_curl}.floatA")
                cmds.setAttr(f"{floatMath_curl}.operation", 2)
                cmds.setAttr(f"{floatMath_curl}.floatB", -9)

                plus_minus = cmds.createNode("plusMinusAverage", name=f"{ctl.replace('_CTL', 'Curl_PMA')}", ss=True)
                cmds.connectAttr(f"{self.hand_attribute_ctl}.rotateZ", f"{plus_minus}.input1D[0]")
                cmds.connectAttr(f"{floatMath_curl}.outFloat", f"{plus_minus}.input1D[1]")

                negate = cmds.createNode("floatMath", name=f"{ctl.replace('_CTL', 'CurlNegate_FLM')}", ss=True)
                cmds.connectAttr(f"{plus_minus}.output1D", f"{negate}.floatA")
                cmds.setAttr(f"{negate}.operation", 2)
                cmds.setAttr(f"{negate}.floatB", -1 * self.value_mult)

                if not "thumb" in ctl or "first" in ctl:

                    floatMathFan_rotation = cmds.createNode("floatMath", name=f"{ctl.replace('_CTL', 'FanRotation_FLM')}", ss=True)
                    cmds.connectAttr(f"{self.hand_attribute_ctl}.rotateX", f"{floatMathFan_rotation}.floatA")
                    cmds.setAttr(f"{floatMathFan_rotation}.operation", 2)

                    floatMath_fan = cmds.createNode("floatMath", name=f"{ctl.replace('_CTL', 'Fan_FLM')}", ss=True)

                    cmds.connectAttr(f"{self.hand_attribute_ctl}.fan", f"{floatMath_fan}.floatA")
                    cmds.setAttr(f"{floatMath_fan}.operation", 2)
                    
                    chain_len = len(guides_chain)
                    if chain_len > 1:
                        base_influence = 0.15 + index * 0.07
                        joint_influence = base_influence + (i / (chain_len - 1)) * (0.5 + index * 0.15)
                        cmds.setAttr(f"{floatMathFan_rotation}.floatB", joint_influence)
                        cmds.setAttr(f"{floatMath_fan}.floatB", joint_influence * 8)
                    else:
                        cmds.setAttr(f"{floatMathFan_rotation}.floatB", 0.0)
                        cmds.setAttr(f"{floatMath_fan}.floatB", 0.0)


                    plus_minus_fan = cmds.createNode("plusMinusAverage", name=f"{ctl.replace('_CTL', 'Curl_PMA')}", ss=True)
                    cmds.connectAttr(f"{floatMathFan_rotation}.outFloat", f"{plus_minus_fan}.input1D[0]")
                    cmds.connectAttr(f"{floatMath_fan}.outFloat", f"{plus_minus_fan}.input1D[1]")

                    floatMath_sum = cmds.createNode("floatMath", name=f"{ctl.replace('_CTL', 'Curl_FLM')}", ss=True)
                    cmds.connectAttr(f"{plus_minus_fan}.output1D", f"{floatMath_sum}.floatA")
                    cmds.connectAttr(f"{negate}.outFloat", f"{floatMath_sum}.floatB")
                    cmds.setAttr(f"{floatMath_sum}.operation", 1)

                    cmds.connectAttr(f"{floatMath_sum}.outFloat", f"{fk_ctls_grps[i][1]}.rotateZ")



            space_switch.fk_switch(target=pv_ctl, sources=[ik_ctl, meta_ctl])
            cmds.setAttr(f"{pv_ctl_grp[0]}.ty", 0)

