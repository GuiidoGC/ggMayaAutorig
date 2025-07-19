#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om

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

            cmds.connectAttr(f"{guide}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")
            cmds.parent(ctl_grp[0], self.fk_ctls[-1] if self.fk_ctls else self.individual_controllers_grp)

            self.fk_ctls.append(ctl)
            self.fk_grps.append(ctl_grp) 
            self.fk_joints.append(joint)

        cmds.addAttr(self.fk_ctls[0], shortName="extraAttr", niceName="Extra Attributes  ———", enumName="_____",attributeType="enum", keyable=True)
        cmds.setAttr(self.fk_ctls[0]+".extraAttr", channelBox=True, lock=True)
        cmds.addAttr(self.fk_ctls[0], shortName="upperTwist", niceName="Upper Twist",defaultValue=0, keyable=True)

        self.ik_rig()

    def create_matrix_pole_vector(self, m1_attr, m2_attr, m3_attr, pole_distance=1.0, name="poleVector_LOC"):
        """
        Given three matrix attributes (e.g. joint.worldMatrix[0]), compute a proper pole vector
        position using Maya matrix and math nodes (no Python vector math).
        """
        def matrix_to_translation(matrix_attr, prefix):
            mm = cmds.createNode('multMatrix', name=f"{self.side}_{self.module_name}PV_MMX", ss=True)
            dm = cmds.createNode('decomposeMatrix', name=f"{self.side}_{self.module_name}PV_DCM", ss=True)
            cmds.connectAttr(matrix_attr, f'{mm}.matrixIn[0]')
            cmds.setAttr(f'{mm}.matrixIn[1]', [1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1], type='matrix')
            cmds.connectAttr(f'{mm}.matrixSum', f'{dm}.inputMatrix')
            return dm, f'{dm}.outputTranslate'

        def create_vector_subtract(name, inputA, inputB):
            node = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}PV_PMA", ss=True)
            cmds.setAttr(f'{node}.operation', 2)
            cmds.connectAttr(inputA, f'{node}.input3D[0]')
            cmds.connectAttr(inputB, f'{node}.input3D[1]')
            return node, f'{node}.output3D'

        def normalize_vector(input_vec, name):
            vp = cmds.createNode('vectorProduct', name=f"{self.side}_{self.module_name}PV_VCP", ss=True)
            cmds.setAttr(f'{vp}.operation', 0)
            cmds.setAttr(f'{vp}.normalizeOutput', 1)
            cmds.connectAttr(input_vec, f'{vp}.input1')
            return vp, f'{vp}.output'

        def scale_vector(input_vec, scalar_attr, name):
            md = cmds.createNode('multiplyDivide', name=f"{self.side}_{self.module_name}PV_MDV", ss=True)
            cmds.setAttr(f'{md}.operation', 1)
            cmds.connectAttr(input_vec, f'{md}.input1')
            for axis in 'XYZ':
                cmds.connectAttr(scalar_attr, f'{md}.input2{axis}')
            return md, f'{md}.output'

        def add_vectors(vecA, vecB, name):
            node = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}PV_PMA", ss=True)
            cmds.connectAttr(vecA, f'{node}.input3D[0]')
            cmds.connectAttr(vecB, f'{node}.input3D[1]')
            return node, f'{node}.output3D'

        dm1, vec1_attr = matrix_to_translation(m1_attr, 'vec1')
        dm2, vec2_attr = matrix_to_translation(m2_attr, 'vec2')
        dm3, vec3_attr = matrix_to_translation(m3_attr, 'vec3')

        dist1 = cmds.createNode('distanceBetween', name=f"{self.side}_{self.module_name}PV_DBT", ss=True)
        cmds.connectAttr(vec1_attr, f'{dist1}.point1')
        cmds.connectAttr(vec2_attr, f'{dist1}.point2')

        dist2 = cmds.createNode('distanceBetween', name=f"{self.side}_{self.module_name}PV_DBT", ss=True)
        cmds.connectAttr(vec2_attr, f'{dist2}.point1')
        cmds.connectAttr(vec3_attr, f'{dist2}.point2')

        avg = cmds.createNode('plusMinusAverage', name=f"{self.side}_{self.module_name}PV_PMA", ss=True)
        cmds.connectAttr(f'{dist1}.distance', f'{avg}.input1D[0]')
        cmds.connectAttr(f'{dist2}.distance', f'{avg}.input1D[1]')

        half = cmds.createNode('multiplyDivide', name=f"{self.side}_{self.module_name}PV_MDV", ss=True)
        cmds.setAttr(f'{half}.operation', 2)
        cmds.setAttr(f'{half}.input2X', 2.0 / pole_distance)
        cmds.connectAttr(f'{avg}.output1D', f'{half}.input1X')

        vec1_sub_node, vec1_sub = create_vector_subtract('vec1_minus_vec2', vec1_attr, vec2_attr)
        vec1_norm_node, vec1_norm = normalize_vector(vec1_sub, 'vec1_norm')

        vec3_sub_node, vec3_sub = create_vector_subtract('vec3_minus_vec2', vec3_attr, vec2_attr)
        vec3_norm_node, vec3_norm = normalize_vector(vec3_sub, 'vec3_norm')

        vec1_scaled_node, vec1_scaled = scale_vector(vec1_norm, f'{half}.outputX', 'vec1_scaled')
        vec3_scaled_node, vec3_scaled = scale_vector(vec3_norm, f'{half}.outputX', 'vec3_scaled')

        vec1_final_node, vec1_final = add_vectors(vec2_attr, vec1_scaled, 'vec1_final')
        vec3_final_node, vec3_final = add_vectors(vec2_attr, vec3_scaled, 'vec3_final')

        proj_dir_node, proj_dir = create_vector_subtract('proj_dir', vec3_final, vec1_final)

        proj_dir_norm_node, proj_dir_norm = normalize_vector(proj_dir, 'proj_dir_norm')

        vec_to_project_node, vec_to_project = create_vector_subtract('vec_to_project', vec2_attr, vec1_final)

        dot_node = cmds.createNode('vectorProduct', name=f"{self.side}_{self.module_name}PV_VCP", ss=True)
        cmds.setAttr(f'{dot_node}.operation', 1)
        cmds.connectAttr(vec_to_project, f'{dot_node}.input1')
        cmds.connectAttr(proj_dir_norm, f'{dot_node}.input2')

        proj_vec_node, proj_vec = scale_vector(proj_dir_norm, f'{dot_node}.outputX', 'proj_vector')

        mid_node, mid = add_vectors(vec1_final, proj_vec, 'mid_point')

        pointer_node, pointer_vec = create_vector_subtract('pointerVec', vec2_attr, mid)

        pointer_norm_node, pointer_norm = normalize_vector(pointer_vec, 'pointerNorm')
        pointer_scaled_node, pointer_scaled = scale_vector(pointer_norm, f'{half}.outputX', 'pointer_scaled')

        pole_pos_node, pole_pos = add_vectors(vec2_attr, pointer_scaled, 'poleVectorPos')

        compose_node = cmds.createNode('composeMatrix', name=f"{self.side}_{self.module_name}PV_CMT", ss=True)
        cmds.connectAttr(pole_pos, f'{compose_node}.inputTranslate')

        return f'{compose_node}.outputMatrix'

    def ik_rig(self):
        """
        Create IK chain for the limb.
        This function creates an inverse kinematics chain for the limb, including controllers and constraints.
        """
        self.ik_controllers = cmds.createNode("transform", name=f"{self.side}_{self.module_name}IkControllers_GRP", parent=self.individual_controllers_grp, ss=True)

        root_ik_ctl, root_ik_ctl_grp = controller_creator(
            name=f"{self.side}_RootIk",
            suffixes=["GRP", "ANM"],
            mirror=self.mirror,
            lock=["sx","sz","sy","visibility"],
            ro=True,
            parent=self.ik_controllers
        )
        pv_ik_ctl, pv_ik_ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}PV",
            suffixes=["GRP", "ANM"],
            mirror=self.mirror,
            lock=["rx", "ry", "rz", "sx","sz","sy","visibility"],
            ro=True,
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

        cmds.addAttr(self.hand_ik_ctl, shortName="extraAttr", niceName="Extra Attributes  ———", enumName="_____",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_ik_ctl+".extraAttr", channelBox=True, lock=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="upperTwist", niceName="Upper Twist",defaultValue=0, keyable=True)

        cmds.addAttr(self.hand_ik_ctl, shortName="ikControls", niceName="IK Controls  ———", enumName="_____",attributeType="enum", keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="curvature", niceName="Curvature", maxValue=1, minValue=0,defaultValue=0, keyable=True)
        cmds.setAttr(self.hand_ik_ctl+".ikControls", channelBox=True, lock=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="soft", niceName="Soft",minValue=0,maxValue=1,defaultValue=0, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="twist", niceName="Twist",minValue=-180,defaultValue=0, maxValue=180, keyable=True)


        cmds.addAttr(self.hand_ik_ctl, shortName="strechySep", niceName="Strechy  ———", enumName="_____",attributeType="enum", keyable=True)
        cmds.setAttr(self.hand_ik_ctl+".strechySep", channelBox=True, lock=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="upperLengthMult", niceName="Upper Length Mult",minValue=0.001,defaultValue=1, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="lowerLengthMult", niceName="Lower Length Mult",minValue=0.001,defaultValue=1, keyable=True)
        cmds.addAttr(self.hand_ik_ctl, shortName="stretch", niceName="Stretch",minValue=0,maxValue=1,defaultValue=0, keyable=True)

        
        

        cmds.connectAttr(f"{self.guides_matrix[0]}.outputMatrix", f"{root_ik_ctl_grp[0]}.offsetParentMatrix")
        cmds.connectAttr(f"{self.guides_matrix[2]}.outputMatrix", f"{self.hand_ik_ctl_grp[0]}.offsetParentMatrix")

        pv_pos = self.create_matrix_pole_vector(
            f"{self.guides_matrix[0]}.outputMatrix",
            f"{self.guides_matrix[1]}.outputMatrix",
            f"{self.guides_matrix[2]}.outputMatrix",
            name=f"{self.side}_{self.module_name}PV"
        )

        cmds.connectAttr(pv_pos, f"{pv_ik_ctl_grp[0]}.offsetParentMatrix")

        cmds.select(clear=True)
        self.ik_chain = [cmds.joint(name=self.guides[0].replace("_GUIDE", "Ik_JNT"), rad=0.5)]
        cmds.parent(self.ik_chain[0], self.individual_module_grp)

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

        cmds.connectAttr(f"{root_ik_ctl}.worldMatrix[0]", f"{self.ik_chain[0]}.offsetParentMatrix")        

        ik_rps = cmds.ikHandle(
            name=f"{self.side}_{self.module_name}Ik_HDL",
            startJoint=self.ik_chain[0],
            endEffector=self.ik_chain[-1],
            solver="ikRPsolver",
        )
        cmds.parent(ik_rps[0], self.individual_module_grp)
        cmds.connectAttr(f"{self.hand_ik_ctl}.twist", f"{ik_rps[0]}.twist")


        float_constant = cmds.createNode("floatConstant", name=f"{self.side}_{self.module_name}IkFloatConstant")
        cmds.setAttr(f"{float_constant}.inFloat", 0)
        cmds.connectAttr(f"{float_constant}.outFloat", f"{ik_rps[0]}.tx")
        cmds.connectAttr(f"{float_constant}.outFloat", f"{ik_rps[0]}.ty")
        cmds.connectAttr(f"{float_constant}.outFloat", f"{ik_rps[0]}.tz")

        cmds.connectAttr(f"{self.hand_ik_ctl}.worldMatrix[0]", f"{ik_rps[0]}.offsetParentMatrix")

        cmds.poleVectorConstraint(pv_ik_ctl, ik_rps[0]) 

        decompose_matrix = cmds.createNode("decomposeMatrix", name=f"{self.side}_{self.module_name}Ik_DPM", ss=True)
        cmds.connectAttr(f"{self.hand_ik_ctl}.matrix", f"{decompose_matrix}.inputMatrix")

        cmds.connectAttr(f"{decompose_matrix}.outputScale", f"{self.ik_chain[-1]}.scale")
        cmds.connectAttr(f"{decompose_matrix}.outputRotate", f"{self.ik_chain[-1]}.rotate")

        """
        
        WIP MATRIX POLE VECTOR

        row_from_matrix = cmds.createNode("rowFromMatrix", name=f"{self.side}_{self.module_name}IkRowFromMatrix")
        cmds.connectAttr(f"{pv_ik_ctl}.worldMatrix[0]", f"{row_from_matrix}.matrix")
        cmds.setAttr(f"{row_from_matrix}.input", 2)
        cmds.connectAttr(f"{row_from_matrix}.outputX", f"{ik_rps[0]}.poleVectorX")
        cmds.connectAttr(f"{row_from_matrix}.outputY", f"{ik_rps[0]}.poleVectorY")
        cmds.connectAttr(f"{row_from_matrix}.outputZ", f"{ik_rps[0]}.poleVectorZ")

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

        blend_two_attrs = cmds.createNode("blendTwoAttr", name=f"{self.side}_{self.module_name}IkFkBlend_BTA", ss=True)
        print(blend_two_attrs)
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

        self.bendy_twist(blend_chain=[self.blend_chain[0], self.blend_chain[1]], suffix=f"{self.side}_upper{self.module_name.capitalize()}Bendy")
        self.bendy_twist(blend_chain=[self.blend_chain[1], self.blend_chain[2]], suffix=f"{self.side}_lower{self.module_name.capitalize()}Bendy")


    def bendy_twist(self, twist_number=5, degree=2, blend_chain=["L_shoulderDr_JNT", "L_elbowDr_JNT"], suffix=f"L_upperArm"):

        ctl, ctl_grp = controller_creator(suffix, suffixes=["GRP", "ANM"], lock=["v"], parent=self.individual_controllers_grp, ro=True)

        blend_matrix = cmds.createNode("blendMatrix", name=f"{suffix}_BLM", ss=True)
        cmds.connectAttr(f"{blend_chain[0]}.worldMatrix[0]", f"{blend_matrix}.inputMatrix")
        cmds.connectAttr(f"{blend_chain[1]}.worldMatrix[0]", f"{blend_matrix}.target[0].targetMatrix")
        cmds.setAttr(f"{blend_matrix}.target[0].weight", 0.5)
        cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].rotateWeight", 0)
        cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)
        cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{ctl_grp[0]}.offsetParentMatrix")



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
                


