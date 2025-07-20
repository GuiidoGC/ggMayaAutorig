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
import gg_autorig.utils.de_boors_core as de_boors

reload(de_boors)
reload(guides_manager)


class LimbModule(object):

    def __init__(self):

        self.side = "L"
        self.module_name = "arm"
        self.first_joint = "shoulder"

        self.mirror = False

        data_exporter = data_export.DataExport()

        self.modules_grp = data_exporter.get_data("basic_structure", "modules_GRP")
        self.skel_grp = data_exporter.get_data("basic_structure", "skel_GRP")
        self.masterWalk_ctl = data_exporter.get_data("basic_structure", "masterWalk_CTL")
        self.guides_grp = data_exporter.get_data("basic_structure", "guides_GRP")

        self.individual_module_grp = cmds.createNode("transform", name=f"{self.side}_{self.module_name}Module_GRP", parent=self.modules_grp, ss=True)
        self.individual_controllers_grp = cmds.createNode("transform", name=f"{self.side}_{self.module_name}Controllers_GRP", parent=self.masterWalk_ctl, ss=True)
        self.skinnging_grp = cmds.createNode("transform", name=f"{self.side}_{self.module_name}SkinningJoints_GRP", parent=self.skel_grp, ss=True)

    

    def create_limb(self):

        """
        Create a limb rig with controllers and constraints.
        This function sets up the basic structure for a limb, including controllers and constraints.
        """        
        self.guides = guide_import(f"{self.side}_{self.first_joint}_GUIDE", all_descendents=True, path=None)

        #Position Joints
        order = [[self.guides[0], self.guides[1], self.guides[2]], [self.guides[1], self.guides[2], self.guides[0]]]

        aim_matrix_guides = []

        for i in range(len(self.guides)-1):

            aim_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_{self.module_name}Guide0{i+1}_AMX", ss=True)
            multmatrix = cmds.createNode("multMatrix", name=f"{self.side}_{self.module_name}GuideOffset0{i+1}_MMX", ss=True)

            cmds.setAttr(aim_matrix + ".primaryInputAxis", 1, 0, 0, type="double3")
            cmds.setAttr(aim_matrix + ".secondaryInputAxis", 0, 0, 1, type="double3")
            
            cmds.setAttr(aim_matrix + ".primaryMode", 1)
            cmds.setAttr(aim_matrix + ".secondaryMode", 1)

            cmds.connectAttr(order[i][0] + ".worldMatrix[0]", aim_matrix + ".inputMatrix")
            cmds.connectAttr(order[i][1] + ".worldMatrix[0]", aim_matrix + ".primaryTargetMatrix")
            cmds.connectAttr(order[i][2] + ".worldMatrix[0]", aim_matrix + ".secondaryTargetMatrix")

            aim_matrix_guides.append(aim_matrix)

        
        blend_matrix = cmds.createNode("blendMatrix", name=f"{self.side}_{self.module_name}Guide03_BLM", ss=True)
        cmds.connectAttr(f"{aim_matrix_guides[1]}.outputMatrix", f"{blend_matrix}.inputMatrix", force=True)
        cmds.connectAttr(f"{self.guides[2]}.worldMatrix[0]", f"{blend_matrix}.target[0].targetMatrix", force=True)
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)

        self.guides_matrix = [aim_matrix_guides[0], aim_matrix_guides[1], blend_matrix]

        self.fk_rig()

    def fk_rig(self):
        """
        Create FK chain for the limb.
        This function creates a forward kinematics chain for the limb, including controllers and constraints.
        """
        self.fk_ctls = []
        self.fk_grps = []
        self.fk_joints = []
        self.fk_offset = []
        for i, guide in enumerate(self.guides_matrix):

            ctl, ctl_grp = controller_creator(
                name=self.guides[i].replace("_GUIDE", "Fk"),
                suffixes=["GRP", "ANM"],
                mirror=self.mirror,
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )

            cmds.select(clear=True)
            joint = cmds.joint(name=self.guides[i].replace("_GUIDE", "Fk_JNT"), rad=0.5)
            cmds.parent(joint, self.individual_module_grp)
            
            cmds.connectAttr(f"{ctl}.worldMatrix[0]", f"{joint}.offsetParentMatrix")

            cmds.parent(ctl_grp[0], self.fk_ctls[-1] if self.fk_ctls else self.individual_controllers_grp)

            if not i == 2:
                cmds.addAttr(ctl, shortName="strechySep", niceName="Strechy ———", enumName="———",attributeType="enum", keyable=True)
                cmds.setAttr(ctl+".strechySep", channelBox=True, lock=True)
                cmds.addAttr(ctl, shortName="stretch", niceName="Stretch",minValue=0.001,defaultValue=1, keyable=True)

            if not i == 0:
                offset_multMatrix = cmds.createNode("multMatrix", name=f"{self.side}_{self.module_name}FkOffset0{i+1}_MMX", ss=True)
                cmds.connectAttr(f"{guide}.outputMatrix", f"{offset_multMatrix}.matrixIn[0]")
                cmds.connectAttr(f"{self.fk_grps[-1][0]}.worldInverseMatrix[0]", f"{offset_multMatrix}.matrixIn[1]")

                decompose_matrix = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}FkOffset0{i+1}_DCM", ss=True)
                compose_matrix = cmds.createNode("composeMatrix", name=f"{self.side}_{self.module_name}FkOffset0{i+1}_CMT", ss=True)

                cmds.connectAttr(f"{offset_multMatrix}.matrixSum", f"{decompose_matrix}.inputMatrix")

                cmds.connectAttr(f"{decompose_matrix}.outputQuat", f"{compose_matrix}.inputQuat")
                cmds.connectAttr(f"{decompose_matrix}.outputRotate", f"{compose_matrix}.inputRotate")
                cmds.connectAttr(f"{decompose_matrix}.outputScale", f"{compose_matrix}.inputScale")
                cmds.connectAttr(f"{decompose_matrix}.outputShear", f"{compose_matrix}.inputShear")
                cmds.connectAttr(f"{decompose_matrix}.outputTranslateY", f"{compose_matrix}.inputTranslateY")
                cmds.connectAttr(f"{decompose_matrix}.outputTranslateZ", f"{compose_matrix}.inputTranslateZ")

                cmds.connectAttr(f"{compose_matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")

                for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                    cmds.setAttr(f"{ctl_grp[0]}.{attr}", 0)

                self.fk_offset.append([decompose_matrix, compose_matrix])

            else:
                cmds.connectAttr(f"{guide}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")




            self.fk_ctls.append(ctl)
            self.fk_grps.append(ctl_grp) 
            self.fk_joints.append(joint)

        cmds.addAttr(self.fk_ctls[0], shortName="extraAttr", niceName="Extra Attributes  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.fk_ctls[0]+".extraAttr", channelBox=True, lock=True)
        cmds.addAttr(self.fk_ctls[0], shortName="upperTwist", niceName="Upper Twist",defaultValue=0, keyable=True)
        cmds.addAttr(self.fk_ctls[0], shortName="curvature", niceName="Curvature", maxValue=1, minValue=0,defaultValue=0, keyable=True)


        self.ik_rig()

    def create_matrix_pole_vector(self, m1_attr, m2_attr, m3_attr, pole_distance=1.0, name="poleVector_LOC"):
        """
        Given three matrix attributes (e.g. joint.worldMatrix[0]), compute a proper pole vector
        position using Maya matrix and math nodes (no Python vector math).
        """
        def matrix_to_translation(matrix_attr, prefix):
            mm = cmds.createNode('multMatrix', name=f"{self.side}_{self.module_name}Pv{prefix.capitalize()}Offset_MMX", ss=True)
            dm = cmds.createNode('decomposeMatrix', name=f"{self.side}_{self.module_name}Pv{prefix.capitalize()}Offset_DCM", ss=True)
            cmds.connectAttr(matrix_attr, f'{mm}.matrixIn[0]')
            cmds.setAttr(f'{mm}.matrixIn[1]', [1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1], type='matrix')
            cmds.connectAttr(f'{mm}.matrixSum', f'{dm}.inputMatrix')
            return dm, f'{dm}.outputTranslate'

        def create_vector_subtract(name, inputA, inputB):
            node = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}Pv{name.capitalize()}_PMA", ss=True)
            cmds.setAttr(f'{node}.operation', 2)
            cmds.connectAttr(inputA, f'{node}.input3D[0]')
            cmds.connectAttr(inputB, f'{node}.input3D[1]')
            return node, f'{node}.output3D'

        def normalize_vector(input_vec, name):
            vp = cmds.createNode('vectorProduct', name=f"{self.side}_{self.module_name}Pv{name.capitalize()}_VCP", ss=True)
            cmds.setAttr(f'{vp}.operation', 0)
            cmds.setAttr(f'{vp}.normalizeOutput', 1)
            cmds.connectAttr(input_vec, f'{vp}.input1')
            return vp, f'{vp}.output'

        def scale_vector(input_vec, scalar_attr, name):
            md = cmds.createNode('multiplyDivide', name=f"{self.side}_{self.module_name}Pv{name.capitalize()}_MDV", ss=True)
            cmds.setAttr(f'{md}.operation', 1)
            cmds.connectAttr(input_vec, f'{md}.input1')
            for axis in 'XYZ':
                cmds.connectAttr(scalar_attr, f'{md}.input2{axis}')
            return md, f'{md}.output'

        def add_vectors(vecA, vecB, name):
            node = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}Pv{name.capitalize()}_PMA", ss=True)
            cmds.connectAttr(vecA, f'{node}.input3D[0]')
            cmds.connectAttr(vecB, f'{node}.input3D[1]')
            return node, f'{node}.output3D'

        dm1, vec1_attr = matrix_to_translation(m1_attr, 'vec1')
        dm2, vec2_attr = matrix_to_translation(m2_attr, 'vec2')
        dm3, vec3_attr = matrix_to_translation(m3_attr, 'vec3')

        dist1 = cmds.createNode('distanceBetween', name=f"{self.side}_{self.module_name}PvVec1Vec2_DBT", ss=True)
        cmds.connectAttr(vec1_attr, f'{dist1}.point1')
        cmds.connectAttr(vec2_attr, f'{dist1}.point2')

        dist2 = cmds.createNode('distanceBetween', name=f"{self.side}_{self.module_name}PvVec2Vec3_DBT", ss=True)
        cmds.connectAttr(vec2_attr, f'{dist2}.point1')
        cmds.connectAttr(vec3_attr, f'{dist2}.point2')

        avg = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}PvAvgDist_PMA", ss=True)
        cmds.connectAttr(f'{dist1}.distance', f'{avg}.input1D[0]')
        cmds.connectAttr(f'{dist2}.distance', f'{avg}.input1D[1]')

        half = cmds.createNode('multiplyDivide', name=f"{self.side}_{self.module_name}PvHalfDist_MDV", ss=True)
        cmds.setAttr(f'{half}.operation', 2)
        cmds.setAttr(f'{half}.input2X', 2.0 / pole_distance)
        cmds.connectAttr(f'{avg}.output1D', f'{half}.input1X')

        vec1_sub_node, vec1_sub = create_vector_subtract('vec1MinusVec2', vec1_attr, vec2_attr)
        vec1_norm_node, vec1_norm = normalize_vector(vec1_sub, 'vec1Norm')

        vec3_sub_node, vec3_sub = create_vector_subtract('vec3MinusVec2', vec3_attr, vec2_attr)
        vec3_norm_node, vec3_norm = normalize_vector(vec3_sub, 'vec3Norm')

        vec1_scaled_node, vec1_scaled = scale_vector(vec1_norm, f'{half}.outputX', 'vec1Scaled')
        vec3_scaled_node, vec3_scaled = scale_vector(vec3_norm, f'{half}.outputX', 'vec3Scaled')

        vec1_final_node, vec1_final = add_vectors(vec2_attr, vec1_scaled, 'vec1Final')
        vec3_final_node, vec3_final = add_vectors(vec2_attr, vec3_scaled, 'vec3Final')

        proj_dir_node, proj_dir = create_vector_subtract('projDir', vec3_final, vec1_final)

        proj_dir_norm_node, proj_dir_norm = normalize_vector(proj_dir, 'projDirNorm')

        vec_to_project_node, vec_to_project = create_vector_subtract('vecToProject', vec2_attr, vec1_final)

        dot_node = cmds.createNode('vectorProduct', name=f"{self.side}_{self.module_name}PvDot_VCP", ss=True)
        cmds.setAttr(f'{dot_node}.operation', 1)
        cmds.connectAttr(vec_to_project, f'{dot_node}.input1')
        cmds.connectAttr(proj_dir_norm, f'{dot_node}.input2')

        proj_vec_node, proj_vec = scale_vector(proj_dir_norm, f'{dot_node}.outputX', 'projVector')

        mid_node, mid = add_vectors(vec1_final, proj_vec, 'midPoint')

        pointer_node, pointer_vec = create_vector_subtract('pointerVec', vec2_attr, mid)

        pointer_norm_node, pointer_norm = normalize_vector(pointer_vec, 'pointerNorm')
        pointer_scaled_node, pointer_scaled = scale_vector(pointer_norm, f'{half}.outputX', 'pointerScaled')

        pole_pos_node, pole_pos = add_vectors(vec2_attr, pointer_scaled, 'poleVectorPos')

        compose_node = cmds.createNode('composeMatrix', name=f"{self.side}_{self.module_name}PvCompose_CMT", ss=True)
        cmds.connectAttr(pole_pos, f'{compose_node}.inputTranslate')

        aim_matrix = cmds.createNode('aimMatrix', name=f"{self.side}_{self.module_name}PvAim_AMX", ss=True)
        cmds.setAttr(f'{aim_matrix}.primaryInputAxis', 0, 0, 1, type='double3')
        cmds.setAttr(f'{aim_matrix}.secondaryInputAxis', 0, 1, 0, type='double3')
        cmds.setAttr(f'{aim_matrix}.secondaryTargetVector', 0, 1, 0, type='double3')
        cmds.setAttr(f'{aim_matrix}.primaryMode', 1)
        cmds.setAttr(f'{aim_matrix}.secondaryMode', 2)
        cmds.connectAttr(f'{compose_node}.outputMatrix', f'{aim_matrix}.inputMatrix')
        cmds.connectAttr(f'{m2_attr}', f"{aim_matrix}.primaryTargetMatrix")
        cmds.connectAttr(f'{m2_attr}', f'{aim_matrix}.secondaryTargetMatrix')

        blend_matrix = cmds.createNode('blendMatrix', name=f"{self.side}_{self.module_name}PvBlend_BLM", ss=True)
        cmds.connectAttr(f'{compose_node}.outputMatrix', f'{blend_matrix}.inputMatrix')
        cmds.connectAttr(f'{aim_matrix}.outputMatrix', f'{blend_matrix}.target[0].targetMatrix')

        return blend_matrix


        return blend_matrix

    def ik_rig(self):
        """
        Create IK chain for the limb.
        This function creates an inverse kinematics chain for the limb, including controllers and constraints.
        """
        self.ik_controllers = cmds.createNode("transform", name=f"{self.side}_{self.module_name}IkControllers_GRP", parent=self.individual_controllers_grp, ss=True)

        self.root_ik_ctl, self.root_ik_ctl_grp = controller_creator(
            name=f"{self.side}_RootIk",
            suffixes=["GRP", "ANM"],
            mirror=self.mirror,
            lock=["sx","sz","sy","visibility"],
            ro=True,
            parent=self.ik_controllers
        )
        self.pv_ik_ctl, self.pv_ik_ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}PV",
            suffixes=["GRP", "ANM"],
            mirror=self.mirror,
            lock=["rx", "ry", "rz", "sx","sz","sy","visibility"],
            ro=False,
            parent=self.ik_controllers

        )
        self.hand_ik_ctl, self.hand_ik_ctl_grp = controller_creator(
            name=f"{self.side}_HandIk",
            suffixes=["GRP", "ANM"],
            mirror=self.mirror,
            lock=["visibility"],
            ro=True,
            parent=self.ik_controllers

        )

        cmds.addAttr(self.hand_ik_ctl, shortName="ikControls", niceName="IK Controls  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="curvature", niceName="Curvature", maxValue=1, minValue=0,defaultValue=0, keyable=True)
        cmds.setAttr(self.hand_ik_ctl+".ikControls", channelBox=True, lock=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="soft", niceName="Soft",minValue=0,maxValue=1,defaultValue=0, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="twist", niceName="Twist",minValue=-180,defaultValue=0, maxValue=180, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="upperTwist", niceName="Upper Twist",defaultValue=0, keyable=True)

        cmds.addAttr(self.hand_ik_ctl, shortName="strechySep", niceName="Strechy  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_ik_ctl+".strechySep", channelBox=True, lock=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="upperLengthMult", niceName="Upper Length Mult",minValue=0.001,defaultValue=1, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="lowerLengthMult", niceName="Lower Length Mult",minValue=0.001,defaultValue=1, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="stretch", niceName="Stretch",minValue=0,maxValue=1,defaultValue=0, keyable=True)

        cmds.addAttr(self.pv_ik_ctl, shortName="extraAttr", niceName="Extra Attributes  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.pv_ik_ctl+".extraAttr", channelBox=True, lock=True)
        cmds.addAttr(self.pv_ik_ctl, shortName="pvOrientation", niceName="Pv Orientation",defaultValue=0, minValue=0, maxValue=1, keyable=True)

        cmds.addAttr(self.pv_ik_ctl, shortName="poleVectorPinning", niceName="Pole Vector Pinning ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.pv_ik_ctl+".poleVectorPinning", channelBox=True, lock=True)
        cmds.addAttr(self.pv_ik_ctl, shortName="pin", niceName="Pin",minValue=0,maxValue=1,defaultValue=0, keyable=True)
        
        cmds.connectAttr(f"{self.guides_matrix[0]}.outputMatrix", f"{self.root_ik_ctl_grp[0]}.offsetParentMatrix")
        cmds.connectAttr(f"{self.guides_matrix[2]}.outputMatrix", f"{self.hand_ik_ctl_grp[0]}.offsetParentMatrix")

        pv_pos = self.create_matrix_pole_vector(
            f"{self.guides_matrix[0]}.outputMatrix",
            f"{self.guides_matrix[1]}.outputMatrix",
            f"{self.guides_matrix[2]}.outputMatrix",
            name=f"{self.side}_{self.module_name}PV"
        )

        cmds.connectAttr(f"{self.pv_ik_ctl}.pvOrientation", f"{pv_pos}.target[0].weight")
        cmds.connectAttr(f"{pv_pos}.outputMatrix", f"{self.pv_ik_ctl_grp[0]}.offsetParentMatrix")

        cmds.select(clear=True)
        self.ik_chain = [cmds.joint(name=self.guides[0].replace("_GUIDE", "Ik_JNT"), rad=0.5)]
        cmds.parent(self.ik_chain[0], self.individual_module_grp)

        self.distance_between_output = []

        for i, guide in enumerate(self.guides_matrix[1:]):
            cmds.select(clear=True)
            joint = cmds.joint(name=self.guides[i+1].replace("_GUIDE", "Ik_JNT"), rad=0.5)
            cmds.parent(joint, self.ik_chain[-1])
            self.ik_chain.append(joint)

            cmds.setAttr(f"{joint}.preferredAngle", 0, -1, 0, type="double3")

            distance_between = cmds.createNode("distanceBetween", name=f"{self.side}_{self.module_name}IkDistance0{i+1}_DB")
            cmds.connectAttr(f"{self.guides_matrix[i]}.outputMatrix", f"{distance_between}.inMatrix1")
            cmds.connectAttr(f"{self.guides_matrix[i+1]}.outputMatrix", f"{distance_between}.inMatrix2")
            cmds.connectAttr(f"{distance_between}.distance", f"{joint}.tx")    
            self.distance_between_output.append(f"{distance_between}.distance")

        cmds.connectAttr(f"{self.root_ik_ctl}.worldMatrix[0]", f"{self.ik_chain[0]}.offsetParentMatrix")        

        self.ik_rps = cmds.ikHandle(
            name=f"{self.side}_{self.module_name}Ik_HDL",
            startJoint=self.ik_chain[0],
            endEffector=self.ik_chain[-1],
            solver="ikRPsolver",
        )
        cmds.parent(self.ik_rps[0], self.individual_module_grp)
        cmds.connectAttr(f"{self.hand_ik_ctl}.twist", f"{self.ik_rps[0]}.twist")


        float_constant = cmds.createNode("floatConstant", name=f"{self.side}_{self.module_name}IkFloatConstant")
        cmds.setAttr(f"{float_constant}.inFloat", 0)
        cmds.connectAttr(f"{float_constant}.outFloat", f"{self.ik_rps[0]}.tx")
        cmds.connectAttr(f"{float_constant}.outFloat", f"{self.ik_rps[0]}.ty")
        cmds.connectAttr(f"{float_constant}.outFloat", f"{self.ik_rps[0]}.tz")

        cmds.connectAttr(f"{self.hand_ik_ctl}.worldMatrix[0]", f"{self.ik_rps[0]}.offsetParentMatrix")

        cmds.poleVectorConstraint(self.pv_ik_ctl, self.ik_rps[0]) 

        mult_matrix = cmds.createNode("multMatrix", name=f"{self.side}_{self.module_name}EndIk_MMX", ss=True)
        cmds.connectAttr(f"{self.hand_ik_ctl}.worldMatrix[0]", f"{mult_matrix}.matrixIn[0]")
        cmds.connectAttr(f"{self.ik_chain[1]}.worldInverseMatrix[0]", f"{mult_matrix}.matrixIn[1]")

        decompose_matrix = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}EndIK_DPM", ss=True)
        cmds.connectAttr(f"{mult_matrix}.matrixSum", f"{decompose_matrix}.inputMatrix")

        cmds.connectAttr(f"{decompose_matrix}.outputScale", f"{self.ik_chain[-1]}.scale")
        cmds.connectAttr(f"{decompose_matrix}.outputRotate", f"{self.ik_chain[-1]}.rotate")

        """
        
        WIP MATRIX POLE VECTOR

        row_from_matrix = cmds.createNode("rowFromMatrix", name=f"{self.side}_{self.module_name}IkRowFromMatrix")
        cmds.connectAttr(f"{self.pv_ik_ctl}.worldMatrix[0]", f"{row_from_matrix}.matrix")
        cmds.setAttr(f"{row_from_matrix}.input", 2)
        cmds.connectAttr(f"{row_from_matrix}.outputX", f"{self.ik_rps[0]}.poleVectorX")
        cmds.connectAttr(f"{row_from_matrix}.outputY", f"{self.ik_rps[0]}.poleVectorY")
        cmds.connectAttr(f"{row_from_matrix}.outputZ", f"{self.ik_rps[0]}.poleVectorZ")

        """

        self.pairblends()

    def pairblends(self):
        """
        Create pair blends for the limb.
        This function sets up pair blends to switch between FK and IK controllers.
        """



        self.switch_pos = guide_import(f"{self.side}_{self.module_name}Settings_GUIDE", all_descendents=False)[0]

        self.switch_ctl, self.switch_ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}Switch",
            suffixes=["GRP"],
            lock=["tx","ty","tz","rx","ry","rz","sx", "sy", "sz", "visibility"],
            ro=False,
            match=self.switch_pos,
            parent=self.individual_controllers_grp
        )

        cmds.delete(self.switch_pos)

        cmds.addAttr(self.switch_ctl, shortName="switchIkFk", niceName="Switch IK --> FK", maxValue=1, minValue=0,defaultValue=0, keyable=True)
        cmds.connectAttr(f"{self.switch_ctl}.switchIkFk", f"{self.fk_grps[0][0]}.visibility", force=True)
        rev = cmds.createNode("reverse", name=f"{self.side}_{self.module_name}FkVisibility_REV", ss=True)
        cmds.connectAttr(f"{self.switch_ctl}.switchIkFk", f"{rev}.inputX")
        cmds.connectAttr(f"{rev}.outputX", f"{self.ik_controllers}.visibility")

        blend_two_attrs = cmds.createNode("blendTwoAttr", name=f"{self.side}_{self.module_name}IkFkBlendNonRoll_BTA", ss=True)
        cmds.connectAttr(f"{self.switch_ctl}.switchIkFk", f"{blend_two_attrs}.attributesBlender")
        cmds.connectAttr(f"{self.fk_ctls[0]}.upperTwist", f"{blend_two_attrs}.input[1]")
        cmds.connectAttr(f"{self.hand_ik_ctl}.upperTwist", f"{blend_two_attrs}.input[0]")


        self.blend_chain = []
        for i, fk_joint in enumerate(self.fk_joints):
            cmds.select(clear=True)
            joint = cmds.joint(name=self.guides[i].replace("_GUIDE", "Blend_JNT"), rad=0.5)
            blendMatrix = cmds.createNode("blendMatrix", name=f"{self.side}_{self.module_name}0{i+1}_BLM", ss=True)
            cmds.connectAttr(f"{self.ik_chain[i]}.worldMatrix[0]", f"{blendMatrix}.inputMatrix")
            cmds.connectAttr(f"{fk_joint}.worldMatrix[0]", f"{blendMatrix}.target[0].targetMatrix")
            cmds.connectAttr(f"{self.switch_ctl}.switchIkFk", f"{blendMatrix}.target[0].weight")
            
            if i == 0:
                decomposeMatrix = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}NonRoll0{i+1}_DCM", ss=True)
                composeMatrix = cmds.createNode("composeMatrix", name=f"{self.side}_{self.module_name}NonRoll0{i+1}_CMT", ss=True)

                cmds.connectAttr(f"{blendMatrix}.outputMatrix", f"{decomposeMatrix}.inputMatrix")
                cmds.connectAttr(f"{decomposeMatrix}.outputQuat", f"{composeMatrix}.inputQuat")
                cmds.connectAttr(f"{decomposeMatrix}.outputRotateY", f"{composeMatrix}.inputRotateY")
                cmds.connectAttr(f"{decomposeMatrix}.outputRotateZ", f"{composeMatrix}.inputRotateZ")
                cmds.connectAttr(f"{blend_two_attrs}.output", f"{composeMatrix}.inputRotateX")
                cmds.connectAttr(f"{decomposeMatrix}.outputScale", f"{composeMatrix}.inputScale")
                cmds.connectAttr(f"{decomposeMatrix}.outputShear", f"{composeMatrix}.inputShear")
                cmds.connectAttr(f"{decomposeMatrix}.outputTranslate", f"{composeMatrix}.inputTranslate")

                cmds.connectAttr(f"{composeMatrix}.outputMatrix", f"{joint}.offsetParentMatrix")

            
            
            else:
                cmds.connectAttr(f"{blendMatrix}.outputMatrix", f"{joint}.offsetParentMatrix")

            cmds.parent(joint, self.individual_module_grp)
            
            
            self.blend_chain.append(joint)

        self.ik_soft_stretch_pin_elbow()

    def ik_soft_stretch_pin_elbow(self):

        self.offset_node=cmds.createNode("transform", name=f"{self.side}_{self.module_name}Soft_OFF", parent=self.individual_module_grp, ss=True)
        self.soft_trn=cmds.createNode("transform", name=f"{self.side}_{self.module_name}Soft_TRN", parent=self.offset_node, ss=True)
        self.ikHandleManager = cmds.createNode("transform", name=f"{self.side}_{self.module_name}IkHandleManager_TRN", parent=self.individual_module_grp, ss=True)
        cmds.connectAttr(f"{self.hand_ik_ctl}.worldMatrix[0]", f"{self.ikHandleManager}.offsetParentMatrix") # This must change when other classes are implemented to match ball ctl

        cmds.matchTransform(self.ikHandleManager, self.ik_chain[2])

        aimMatrix = cmds.createNode("aimMatrix", name=f"{self.side}_{self.module_name}Soft_AMX", ss=True)
        cmds.connectAttr(f"{self.root_ik_ctl}.worldMatrix[0]", f"{aimMatrix}.inputMatrix")
        cmds.connectAttr(f"{self.ikHandleManager}.worldMatrix[0]", f"{aimMatrix}.primaryTargetMatrix")

        cmds.connectAttr(f"{aimMatrix}.outputMatrix", f"{self.offset_node}.offsetParentMatrix")

        nodes_to_create = {
            f"{self.side}_{self.module_name}DistanceToControl_DBT": ("distanceBetween", None), #0
            f"{self.side}_{self.module_name}DistanceToControlNormalized_DBT": ("floatMath", 3), #1
            f"{self.side}_{self.module_name}UpperLength_FLM": ("floatMath", 2), #2
            f"{self.side}_{self.module_name}FullLength_FLM": ("floatMath", 0), #3
            f"{self.side}_{self.module_name}LowerLength_FLM": ("floatMath", 2), #4
            f"{self.side}_{self.module_name}SoftValue_RMV": ("remapValue", None), #5
            f"{self.side}_{self.module_name}SoftDistance_FLM": ("floatMath", 1), #6
            f"{self.side}_{self.module_name}DistanceToControlMinusSoftDistance_FLM": ("floatMath", 1), #7
            f"{self.side}_{self.module_name}DistanceToControlMinusSoftDistanceDividedBySoftValue_FLM": ("floatMath", 3),#8
            f"{self.side}_{self.module_name}DistanceToControlMinusSoftDistanceDividedBySoftValueNegate_FLM": ("floatMath", 2), #9
            f"{self.side}_{self.module_name}SoftEPower_FLM": ("floatMath", 6), #10
            f"{self.side}_{self.module_name}SoftOneMinusEPower_FLM": ("floatMath", 1), #11
            f"{self.side}_{self.module_name}SoftOneMinusEPowerSoftValueEnable_FLM": ("floatMath", 2), #12
            f"{self.side}_{self.module_name}SoftConstant_FLM": ("floatMath", 0), #13
            f"{self.side}_{self.module_name}SoftRatio_FLM": ("floatMath", 3), #14
            f"{self.side}_{self.module_name}LengthRatio_FLM": ("floatMath", 3), #15
            f"{self.side}_{self.module_name}DistanceToControlDividedByTheLengthRatio_FLM": ("floatMath", 3), #16
            f"{self.side}_{self.module_name}SoftEffectorDistance_FLM": ("floatMath", 2), #17
            f"{self.side}_{self.module_name}SoftCondition_CON": ("condition", None), #18
            f"{self.side}_{self.module_name}DistanceToControlDividedByTheSoftEffectorMinusOne_FLM": ("floatMath", 1), #19 
            f"{self.side}_{self.module_name}DistanceToControlDividedByTheSoftEffectorMinusOneMultipliedByTheStretch_FLM": ("floatMath", 2), #20 
            f"{self.side}_{self.module_name}StretchFactor_FLM": ("floatMath", 0), #21 
            f"{self.side}_{self.module_name}SoftEffectStretchDistance_FLM": ("floatMath", 2), #22 
            f"{self.side}_{self.module_name}UpperLengthStretch_FLM": ("floatMath", 2), #23 
            f"{self.side}_{self.module_name}LowerLengthStretch_FLM": ("floatMath", 2), #24 
            f"{self.side}_{self.module_name}DistanceToControlDividedByTheSoftEffector_FLM": ("floatMath", 3), #25
            f"{self.side}_{self.module_name}UpperPin_DBT": ("distanceBetween", None), #26
            f"{self.side}_{self.module_name}LowerPin_DBT": ("distanceBetween", None), #27
            f"{self.side}_{self.module_name}UpperPin_BTA": ("blendTwoAttr", None), #28
            f"{self.side}_{self.module_name}LowerPin_BTA": ("blendTwoAttr", None), #29
            
        }




        created_nodes = []
        for node_name, (node_type, operation) in nodes_to_create.items():
            node = cmds.createNode(node_type, name=node_name)
            created_nodes.append(node)
            if operation is not None:
                cmds.setAttr(f'{node}.operation', operation)

        # Connections between selected nodes
        cmds.connectAttr(created_nodes[0] + ".distance", created_nodes[1]+".floatA")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[15]+".floatA")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[7]+".floatA")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[16]+".floatA")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[18]+".firstTerm")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[18]+".colorIfFalseR")
        cmds.connectAttr(created_nodes[2] + ".outFloat", created_nodes[18]+".colorIfFalseG")
        cmds.connectAttr(created_nodes[2] + ".outFloat", created_nodes[3]+".floatA")
        cmds.connectAttr(created_nodes[3] + ".outFloat", created_nodes[14]+".floatB")
        cmds.connectAttr(created_nodes[3] + ".outFloat", created_nodes[6]+".floatA")
        cmds.connectAttr(created_nodes[3] + ".outFloat", created_nodes[15]+".floatB")
        cmds.connectAttr(created_nodes[4] + ".outFloat", created_nodes[3]+".floatB")
        cmds.connectAttr(created_nodes[4] + ".outFloat", created_nodes[18]+".colorIfFalseB")
        cmds.connectAttr(created_nodes[5] + ".outValue", created_nodes[8]+".floatB")
        cmds.connectAttr(created_nodes[5] + ".outValue", created_nodes[6]+".floatB")
        cmds.connectAttr(created_nodes[5] + ".outValue", created_nodes[12]+".floatA")
        cmds.connectAttr(created_nodes[6] + ".outFloat", created_nodes[13]+".floatB")
        cmds.connectAttr(created_nodes[6] + ".outFloat", created_nodes[7]+".floatB")
        cmds.connectAttr(created_nodes[6] + ".outFloat", created_nodes[18]+".secondTerm")
        cmds.connectAttr(created_nodes[7] + ".outFloat", created_nodes[8]+".floatA")
        cmds.connectAttr(created_nodes[8] + ".outFloat", created_nodes[9]+".floatA")
        cmds.connectAttr(created_nodes[9] + ".outFloat", created_nodes[10]+".floatB")
        cmds.connectAttr(created_nodes[10] + ".outFloat", created_nodes[11]+".floatB")
        cmds.connectAttr(created_nodes[11] + ".outFloat", created_nodes[12]+".floatB")
        cmds.connectAttr(created_nodes[12] + ".outFloat", created_nodes[13]+".floatA")
        cmds.connectAttr(created_nodes[13] + ".outFloat", created_nodes[14]+".floatA")
        cmds.connectAttr(created_nodes[14] + ".outFloat", created_nodes[17]+".floatA")
        cmds.connectAttr(created_nodes[15] + ".outFloat", created_nodes[16]+".floatB")
        cmds.connectAttr(created_nodes[16] + ".outFloat", created_nodes[17]+".floatB")

        cmds.connectAttr(created_nodes[19] + ".outFloat", created_nodes[20]+".floatA")
        cmds.connectAttr(created_nodes[20] + ".outFloat", created_nodes[21]+".floatA")
        cmds.connectAttr(created_nodes[21] + ".outFloat", created_nodes[23]+".floatA")
        cmds.connectAttr(created_nodes[21] + ".outFloat", created_nodes[22]+".floatB")
        cmds.connectAttr(created_nodes[21] + ".outFloat", created_nodes[24]+".floatB")
        cmds.connectAttr(created_nodes[1] + ".outFloat", created_nodes[25]+".floatA")
        cmds.connectAttr(created_nodes[17] + ".outFloat", created_nodes[25]+".floatB")
        cmds.connectAttr(created_nodes[17] + ".outFloat", created_nodes[22]+".floatA")

        cmds.connectAttr(created_nodes[25] + ".outFloat", created_nodes[19]+".floatA")

        cmds.connectAttr(created_nodes[2] + ".outFloat", created_nodes[23]+".floatB")
        cmds.connectAttr(created_nodes[4] + ".outFloat", created_nodes[24]+".floatA")

        cmds.connectAttr(self.hand_ik_ctl + ".stretch", created_nodes[20]+".floatB")

        cmds.connectAttr(created_nodes[22] + ".outFloat", created_nodes[18]+".colorIfTrueR")
        cmds.connectAttr(created_nodes[23] + ".outFloat", created_nodes[18]+".colorIfTrueG")
        cmds.connectAttr(created_nodes[24] + ".outFloat", created_nodes[18]+".colorIfTrueB")

        print(f"Created nodes: {created_nodes[18]}")


        # Connections TRN and nodes

        cmds.connectAttr(f"{self.root_ik_ctl}.worldMatrix", f"{created_nodes[0]}.inMatrix1")
        cmds.connectAttr(f"{self.ikHandleManager}.worldMatrix", f"{created_nodes[0]}.inMatrix2")
        cmds.connectAttr(f"{self.hand_ik_ctl}.lowerLengthMult", f"{created_nodes[4]}.floatA")
        cmds.connectAttr(f"{self.hand_ik_ctl}.upperLengthMult", f"{created_nodes[2]}.floatA")
        cmds.connectAttr(f"{self.hand_ik_ctl}.soft", f"{created_nodes[5]}.inputValue")
        cmds.connectAttr(f"{self.masterWalk_ctl}.globalScale", f"{created_nodes[1]}.floatB")
        cmds.connectAttr(f"{created_nodes[18]}.outColorR",f"{self.soft_trn}.translateX")

        # setAttr nodes



        # cmds.setAttr(f"{created_nodes[2]}.floatB", abs(cmds.getAttr(f"{self.ik_chain[1]}.translateX")))
        # cmds.setAttr(f"{created_nodes[4]}.floatB", abs(cmds.getAttr(f"{self.ik_chain[2]}.translateX")))

        cmds.connectAttr(self.distance_between_output[0], f"{created_nodes[2]}.floatB")
        cmds.connectAttr(self.distance_between_output[1], f"{created_nodes[4]}.floatB")


        cmds.setAttr(f"{created_nodes[9]}.floatB", -1)
        cmds.setAttr(f"{created_nodes[10]}.floatA", math.e)
        cmds.setAttr(f"{created_nodes[11]}.floatA", 1)
        cmds.setAttr(f"{created_nodes[5]}.inputMin", 0.001)
        cmds.setAttr(f"{created_nodes[5]}.outputMax", (cmds.getAttr(f"{created_nodes[3]}.outFloat") - cmds.getAttr(f"{created_nodes[1]}.outFloat")))
        cmds.setAttr(f"{created_nodes[18]}.operation", 2)
        cmds.setAttr(f"{created_nodes[19]}.floatB", 1)


        #Pin 

        cmds.connectAttr(created_nodes[18] + ".outColorG", created_nodes[28]+".input[0]")
        cmds.connectAttr(created_nodes[18] + ".outColorB", created_nodes[29]+".input[0]")

        cmds.connectAttr(self.pv_ik_ctl + ".pin", created_nodes[28]+".attributesBlender")
        cmds.connectAttr(created_nodes[26] + ".distance", created_nodes[28]+".input[1]")
        cmds.connectAttr(self.root_ik_ctl + ".worldMatrix", created_nodes[26]+".inMatrix1")
        cmds.connectAttr(self.pv_ik_ctl + ".worldMatrix", created_nodes[26]+".inMatrix2")

        cmds.connectAttr(self.pv_ik_ctl + ".pin", created_nodes[29]+".attributesBlender")
        cmds.connectAttr(created_nodes[27] + ".distance", created_nodes[29]+".input[1]")
        cmds.connectAttr(self.pv_ik_ctl + ".worldMatrix", created_nodes[27]+".inMatrix2")
        cmds.connectAttr(self.soft_trn + ".worldMatrix", created_nodes[27]+".inMatrix1")

        # cmds.disconnectAttr(f"{self.pv_ik_ctl}.worldMatrix[0]", f"{self.ik_rps[0]}.offsetParentMatrix")        
        cmds.connectAttr(f"{self.ikHandleManager}.worldMatrix[0]", f"{self.ik_rps[0]}.offsetParentMatrix", force=True)



        # if self.side == "R_" and self.module == "arm" or self.side == "R_" and self.module == "leg":
        #     Upper = cmds.createNode("floatMath", name=f"{self.side}{self.module_name}UpperArmPinNegate_FLM")
        #     Lower = cmds.createNode("floatMath", name=f"{self.side}{self.module_name}LowerArmPinNegate_FLM")

        #     cmds.connectAttr(created_nodes[28] + ".output", Upper+".floatA")
        #     cmds.connectAttr(created_nodes[29] + ".output", Lower+".floatA")
        #     cmds.setAttr(Upper+".operation", 2)
        #     cmds.setAttr(Lower+".operation", 2)
        #     cmds.setAttr(Upper+".floatB", -1)
        #     cmds.setAttr(Lower+".floatB", -1)

        #     cmds.connectAttr(Upper + ".outFloat", self.ik_chain[1]+".translateX")
        #     cmds.connectAttr(Lower + ".outFloat", self.ik_chain[2]+".translateX")
        # else:
        cmds.connectAttr(created_nodes[28] + ".output", self.ik_chain[1]+".translateX", f=True)
        cmds.connectAttr(created_nodes[29] + ".output", self.ik_chain[2]+".translateX", f=True)
            

        upper_mult = cmds.createNode("multDoubleLinear", name=f"{self.side}_{self.module_name}FkUpperLengthMult_MDL")
        lower_mult = cmds.createNode("multDoubleLinear", name=f"{self.side}_{self.module_name}FkLowerLengthMult_MDL")

        cmds.connectAttr(f"{self.fk_offset[0][0]}.outputTranslateX", f"{upper_mult}.input2")
        cmds.connectAttr(f"{self.fk_offset[1][0]}.outputTranslateX", f"{lower_mult}.input2")

        cmds.connectAttr(f"{self.fk_ctls[0]}.stretch", upper_mult+".input1")
        cmds.connectAttr(f"{self.fk_ctls[1]}.stretch", lower_mult+".input1")

        cmds.connectAttr(f"{upper_mult}.output", f"{self.fk_offset[0][1]}.inputTranslateX")    
        cmds.connectAttr(f"{lower_mult}.output", f"{self.fk_offset[1][1]}.inputTranslateX")

        self.curvature()

    def curvature(self):
       
        pos = []
        for joint in  self.blend_chain:
            cv_pos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
            pos.append(cv_pos)

        linearArmCurve = cmds.curve(p=pos, d=1)


        # # Bezier curve
        bezierArmCurve = cmds.duplicate(linearArmCurve, name="bezierArmCurve", renameChildren=True)

        cmds.select(bezierArmCurve[0], r=True)
        cmds.nurbsCurveToBezier()
        cmds.select(bezierArmCurve[0] + ".cv[*]", r=True)
        cmds.bezierAnchorPreset(preset=2)
        cmds.select(bezierArmCurve[0] + ".cv[3]", r=True)
        cmds.bezierAnchorPreset(preset=0)
        cmds.bezierAnchorState(smooth=True, even=True)
        

        # Degree Curve

        self.degree2 = cmds.duplicate(linearArmCurve, name=f"{self.side}_{self.module_name}Curvature_CRV", renameChildren=True)
        cmds.rebuildCurve(self.degree2, s=2, d=2)

        upperCurveLoc = cmds.createNode("transform", name=f"{self.side}{self.module_name}UpperCurvature_TRN", ss=True)
        lowerCurveLoc = cmds.createNode("transform", name=f"{self.side}{self.module_name}LowerCurvature_TRN", ss=True)
        midCurveLoc = cmds.createNode("transform", name=f"{self.side}{self.module_name}MidCurvature_TRN", ss=True)

        cv_UpperLoc = cmds.createNode("transform", name=f"{self.side}{self.module_name}UpperCurvatureCV_TRN", ss=True)
        cv_lowerLoc = cmds.createNode("transform", name=f"{self.side}{self.module_name}LowerCurvatureCV_TRN", ss=True)

        # Set upper and lower curve locator positions from bezier curve CVs
        for idx, loc in zip([2, 4], [upperCurveLoc, lowerCurveLoc]):
            pos = cmds.xform(f'{bezierArmCurve[0]}.cv[{idx}]', q=True, t=True)
            for axis, value in zip("XYZ", pos):
                cmds.setAttr(f"{loc}.translate{axis}", value)

        blend_matrix = cmds.createNode("blendMatrix", name=f"{self.side}{self.module_name}CurvatureBlend_MTX", ss=True)
        cmds.connectAttr(f"{self.blend_chain[1]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{self.blend_chain[0]}.worldMatrix[0]", f"{blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix}.target[0].weight", 0.5)
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].translateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)
        cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{midCurveLoc}.offsetParentMatrix")

        upper_pick_matrix = cmds.createNode("pickMatrix", name=f"{self.side}{self.module_name}UpperCurvature_PMX", ss=True)
        lower_pick_matrix = cmds.createNode("pickMatrix", name=f"{self.side}{self.module_name}LowerCurvature_PMX", ss=True)

        for attr in ["useRotate", "useScale", "useShear"]:
            cmds.setAttr(f"{upper_pick_matrix}.{attr}", 0)
            cmds.setAttr(f"{lower_pick_matrix}.{attr}", 0)

        cmds.connectAttr(f"{upperCurveLoc}.worldMatrix[0]", f"{upper_pick_matrix}.inputMatrix")
        cmds.connectAttr(f"{lowerCurveLoc}.worldMatrix[0]", f"{lower_pick_matrix}.inputMatrix")
        cmds.connectAttr(f"{upper_pick_matrix}.outputMatrix", f"{cv_UpperLoc}.offsetParentMatrix")
        cmds.connectAttr(f"{lower_pick_matrix}.outputMatrix", f"{cv_lowerLoc}.offsetParentMatrix")

        

      
        cmds.parent(upperCurveLoc, lowerCurveLoc, midCurveLoc)

        blend_two_attrs = cmds.createNode("blendTwoAttr", name=f"{self.side}{self.module_name}CurvatureBlend_BTA", ss=True)
        cmds.connectAttr(f"{self.switch_ctl}.switchIkFk", f"{blend_two_attrs}.attributesBlender")
        cmds.connectAttr(f"{self.hand_ik_ctl}.curvature", f"{blend_two_attrs}.input[0]")
        cmds.connectAttr(f"{self.fk_ctls[0]}.curvature", f"{blend_two_attrs}.input[1]")

        for axe in ["X", "Y", "Z"]:
            cmds.connectAttr(f"{blend_two_attrs}.output", f"{midCurveLoc}.scale{axe}")


        for i, joint in enumerate([self.blend_chain[0], cv_UpperLoc, cv_lowerLoc,self.blend_chain[2]]):
            decompose = cmds.createNode("decomposeMatrix", name=f"{self.side}{self.module_name}CurvatureCV0{i}_DCM")
            cmds.connectAttr(f"{joint}.worldMatrix", f"{decompose}.inputMatrix")
            cmds.connectAttr(f"{decompose}.outputTranslate", f"{self.degree2[0]}.controlPoints[{i}]")

        cmds.delete(linearArmCurve, bezierArmCurve)
        
        curvature_module = cmds.createNode("transform", name=f"{self.side}{self.module_name}Curvature_GRP", parent=self.individual_module_grp, ss=True)

        cmds.parent(self.degree2, midCurveLoc, cv_UpperLoc, cv_lowerLoc, curvature_module)

        self.detach_curve = cmds.detachCurve(f"{self.degree2[0]}.u[1]",ch=True, rpo=False,cos=True ,name=f"{self.side}_{self.module_name}UpperSegment_CRV")

        self.detach_curve[0] = cmds.rename(self.detach_curve[0], f"{self.side}_{self.module_name}UpperSegment_CRV")
        self.detach_curve[1] = cmds.rename(self.detach_curve[1], f"{self.side}_{self.module_name}LowerSegment_CRV")

        cmds.parent(self.detach_curve[0],self.detach_curve[1], curvature_module)

        self.bendy_ctls = []
        self.bendy_ctls_grp = []

        for i, (curve, name) in enumerate(zip([self.detach_curve[0], self.detach_curve[1]], ["UpperSegment", "LowerSegment"])):
            mpa = cmds.createNode("motionPath", name=f"{self.side}_{self.module_name}{name}_MTP", ss=True)
            cmds.connectAttr(f"{curve}.worldSpace[0]", f"{mpa}.geometryPath")
            cmds.setAttr(f"{mpa}.fractionMode", True)
            cmds.setAttr(f"{mpa}.uValue", 0.5)

            ctl, ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}{name}Bendy",
            suffixes=["GRP", "ANM"],
            lock=["v"],
            parent=self.individual_controllers_grp,
            ro=True
            )

            blend_matrix = cmds.createNode("blendMatrix", name=f"{self.side}_{self.module_name}{name}Bendy_BLM", ss=True)
            cmds.connectAttr(f"{self.blend_chain[i]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
            cmds.connectAttr(f"{self.blend_chain[i+1]}.worldMatrix[0]", f"{blend_matrix}.target[0].targetMatrix")
            cmds.setAttr(f"{blend_matrix}.target[0].weight", 0.5)
            cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
            cmds.setAttr(f"{blend_matrix}.target[0].rotateWeight", 0)
            cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)
            # cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")

            decompose = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}{name}Bendy_DCM", ss=True)
            cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{decompose}.inputMatrix")

            compose = cmds.createNode("composeMatrix", name=f"{self.side}_{self.module_name}{name}Bendy_CPM", ss=True)
            cmds.connectAttr(f"{mpa}.allCoordinates", f"{compose}.inputTranslate")
            cmds.connectAttr(f"{decompose}.outputRotate", f"{compose}.inputRotate")
            cmds.connectAttr(f"{decompose}.outputScale", f"{compose}.inputScale")
            cmds.connectAttr(f"{decompose}.outputShear", f"{compose}.inputShear")
            cmds.connectAttr(f"{decompose}.outputQuat", f"{compose}.inputQuat")

            cmds.connectAttr(f"{compose}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")

            self.bendy_twist(blend_chain=[self.blend_chain[i], self.blend_chain[i+1]], ctl = ctl, suffix=f"{self.side}_{self.module_name}{name}Bendy")

            self.bendy_ctls.append(ctl)
            self.bendy_ctls_grp.append(ctl_grp)





    def bendy_twist(self, twist_number=5, degree=2, blend_chain=["L_shoulderDr_JNT", "L_elbowDr_JNT"],ctl="bendy_ctl",  suffix=f"L_upperArm"):
    
        cvMatrices = [f"{driver}.worldMatrix[0]" for driver in [blend_chain[0], ctl, blend_chain[1]]]

        joints = []

        for i in range(twist_number):
            t = 0.95 if i == twist_number - 1 else i / (float(twist_number) - 1)
            cmds.select(clear=True)
            joint = cmds.joint(name=f"{suffix}0{i+1}_JNT", rad=0.5)
            cmds.parent(joint, self.skinnging_grp)


            pointMatrixWeights = de_boors.pointOnCurveWeights(cvMatrices, t, degree=degree)

            pma_node = cmds.createNode('plusMinusAverage', name=f"{suffix}0{i+1}_PMA", ss=True)
            cmds.setAttr(f"{pma_node}.operation", 1)

            cube = cmds.polyCube(name=f"pJoint{i}_cube", width=1, height=1, depth=1)[0]   
            cmds.parent(cube, joint)
        
            pointMatrixNode = cmds.createNode("wtAddMatrix", name=f"{suffix}0{i+1}_PMX", ss=True)
            pointMatrix = f"{pointMatrixNode}.matrixSum"

            # Scale preservation
            for index, (matrix, weight) in enumerate(pointMatrixWeights):
                md = cmds.createNode('multiplyDivide', name=f"{suffix}0{i+1}_MDV", ss=True)
                cmds.setAttr(f"{md}.input2X", weight)
                cmds.setAttr(f"{md}.input2Y", weight)
                cmds.setAttr(f"{md}.input2Z", weight)
                decomposeNode = cmds.createNode("decomposeMatrix", name=f"{suffix}Scale0{i+1}_DCM", ss=True)
                cmds.connectAttr(f"{matrix}", f"{decomposeNode}.inputMatrix", force=True)
                cmds.connectAttr(f"{decomposeNode}.outputScale", f"{md}.input1", force=True)               

                cmds.connectAttr(f"{md}.output", f"{pma_node}.input3D[{index}]", force=True)

            # Joint positioning
            for index, (matrix, weight) in enumerate(pointMatrixWeights):
                cmds.connectAttr(matrix, f"{pointMatrixNode}.wtMatrix[{index}].matrixIn")
                float_constant = cmds.createNode("floatConstant", name=f"{suffix}Point0{i+1}_FLM", ss=True)
                cmds.setAttr(f"{float_constant}.inFloat", weight)
                cmds.connectAttr(f"{float_constant}.outFloat", f"{pointMatrixNode}.wtMatrix[{index}].weightIn", force=True)
            
            # Joint Tangent Matrix
            tangentMatrixWeights = de_boors.tangentOnCurveWeights(cvMatrices, t, degree=degree)
            
            tangentMatrixNode = cmds.createNode("wtAddMatrix", name=f"{suffix}Tangent0{i+1}_WTADD", ss=True)
            tangentMatrix = f"{tangentMatrixNode}.matrixSum"
            for index, (matrix, weight) in enumerate(tangentMatrixWeights):
                cmds.connectAttr(matrix, f"{tangentMatrixNode}.wtMatrix[{index}].matrixIn")
                float_constant = cmds.createNode("floatConstant", name=f"{suffix}Tangent0{i+1}_FLM", ss=True)
                cmds.setAttr(f"{float_constant}.inFloat", weight)
                cmds.connectAttr(f"{float_constant}.outFloat", f"{tangentMatrixNode}.wtMatrix[{index}].weightIn", force=True)

            aimMatrixNode = cmds.createNode("aimMatrix", name=f"{suffix}0{i+1}_AMX", ss=True)
            cmds.connectAttr(pointMatrix, f"{aimMatrixNode}.inputMatrix")
            cmds.connectAttr(tangentMatrix, f"{aimMatrixNode}.primaryTargetMatrix")
            cmds.setAttr(f"{aimMatrixNode}.primaryMode", 1)
            cmds.setAttr(f"{aimMatrixNode}.primaryInputAxis", 1, 0, 0)
            cmds.setAttr(f"{aimMatrixNode}.secondaryInputAxis", 0, 1, 0)
            cmds.setAttr(f"{aimMatrixNode}.secondaryMode", 0)
            aimMatrixOutput = f"{aimMatrixNode}.outputMatrix"

            pickMatrixNode = cmds.createNode("pickMatrix", name=f"{suffix}0{i+1}_PKMX", ss=True)
            cmds.connectAttr(aimMatrixOutput, f"{pickMatrixNode}.inputMatrix")
            cmds.setAttr(f"{pickMatrixNode}.useScale", False)
            cmds.setAttr(f"{pickMatrixNode}.useShear", False)
            outputMatrix = f"{pickMatrixNode}.outputMatrix"

            decomposeNode = cmds.createNode("decomposeMatrix", name=f"{suffix}0{i+1}_DCM", ss=True)
            cmds.connectAttr(outputMatrix, f"{decomposeNode}.inputMatrix")

            composeNode = cmds.createNode("composeMatrix", name=f"{suffix}0{i+1}_CPM", ss=True)
            cmds.connectAttr(f"{decomposeNode}.outputTranslate", f"{composeNode}.inputTranslate")   
            cmds.connectAttr(f"{decomposeNode}.outputRotate", f"{composeNode}.inputRotate")

            cmds.connectAttr(f"{pma_node}.output3D", f"{composeNode}.inputScale", force=True)



            cmds.connectAttr(f"{composeNode}.outputMatrix", f"{joint}.offsetParentMatrix")

            

            joints.append(joint)

        if "lower" in suffix:
                cmds.select(clear=True)
                joint = cmds.joint(name=f"{suffix}0{i+2}_JNT", rad=0.5)
                cmds.parent(joint, self.skinnging_grp)
                cube = cmds.polyCube(name=f"pJoint{i}_cube", width=1, height=1, depth=1)[0]   
                cmds.parent(cube, joint)
                cmds.connectAttr(f"{blend_chain[-1]}.worldMatrix[0]", f"{joint}.offsetParentMatrix")
                


