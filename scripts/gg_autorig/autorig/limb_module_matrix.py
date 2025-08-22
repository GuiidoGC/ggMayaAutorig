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
from gg_autorig.utils import space_switch as ss
from gg_autorig.utils import core
from gg_autorig.utils import basic_structure


reload(de_boors)
reload(guides_manager)
reload(ss)


class LimbModule(object):

    def __init__(self, side="L"):

        self.side = side
        self.module_name = "arm"
        self.guides = []
        self.scapula_guide = None
        self.enum_str = None

        self.primary_aim = (1, 0, 0)
        self.secondary_aim = (0, 0, 1) 
        self.prefered_angle = (0, -1, 0) 

        self.default_ik = 1
        self.oriented_ik = False


        self.data_exporter = data_export.DataExport()

        self.modules_grp = self.data_exporter.get_data("basic_structure", "modules_GRP")
        self.skel_grp = self.data_exporter.get_data("basic_structure", "skel_GRP")
        self.masterWalk_ctl = self.data_exporter.get_data("basic_structure", "masterWalk_CTL")
        self.guides_grp = self.data_exporter.get_data("basic_structure", "guides_GRP")


    def make(self):

        """
        Create a limb rig with controllers and constraints.
        This function sets up the basic structure for a limb, including controllers and constraints.
        """      

        self.individual_module_grp = cmds.createNode("transform", name=f"{self.side}_{self.module_name}Module_GRP", parent=self.modules_grp, ss=True)
        self.individual_controllers_grp = cmds.createNode("transform", name=f"{self.side}_{self.module_name}Controllers_GRP", parent=self.masterWalk_ctl, ss=True)
        self.skinnging_grp = cmds.createNode("transform", name=f"{self.side}_{self.module_name}SkinningJoints_GRP", parent=self.skel_grp, ss=True)

        cmds.addAttr(self.skinnging_grp, longName="moduleName", attributeType="enum", enumName=self.enum_str, keyable=False)

        #Position Joints
        order = [[self.guides[0], self.guides[1], self.guides[2]], [self.guides[1], self.guides[2], self.guides[0]]]


        aim_matrix_guides = []

        for i in range(len(self.guides)-1):

            aim_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_{self.module_name}Guide0{i+1}_AMX", ss=True)
            multmatrix = cmds.createNode("multMatrix", name=f"{self.side}_{self.module_name}GuideOffset0{i+1}_MMX", ss=True)

            cmds.setAttr(aim_matrix + ".primaryInputAxis", *self.primary_aim, type="double3")
            cmds.setAttr(aim_matrix + ".secondaryInputAxis", *self.secondary_aim, type="double3")
            
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
                cmds.addAttr(ctl, shortName="stretch", niceName="Stretch",minValue=1,defaultValue=1, keyable=True)

                

            if not i == 0:
                subtract = cmds.createNode("subtract", name=f"{self.side}_{self.module_name}FkOffset0{i}_SUB", ss=True)
                cmds.connectAttr(f"{self.fk_ctls[-1]}.stretch", f"{subtract}.input1")
                cmds.setAttr( f"{subtract}.input2", 1)
                cmds.connectAttr(f"{subtract}.output", f"{ctl_grp[0]}.tx")
                

                offset_multMatrix = cmds.createNode("multMatrix", name=f"{self.side}_{self.module_name}FkOffset0{i+1}_MMX", ss=True)
                inverse_matrix = cmds.createNode("inverseMatrix", name=f"{self.side}_{self.module_name}FkOffset0{i+1}_IMX", ss=True)
                cmds.connectAttr(f"{guide}.outputMatrix", f"{offset_multMatrix}.matrixIn[0]")

                cmds.connectAttr(f"{self.guides_matrix[i-1]}.outputMatrix", f"{inverse_matrix}.inputMatrix")

                cmds.connectAttr(f"{inverse_matrix}.outputMatrix", f"{offset_multMatrix}.matrixIn[1]")
            

                cmds.connectAttr(f"{offset_multMatrix}.matrixSum", f"{ctl_grp[0]}.offsetParentMatrix")


                for attr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                    try:
                        cmds.setAttr(f"{ctl_grp[0]}.{attr}", 0)
                    except:
                        pass

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
            # mm = cmds.createNode('multMatrix', name=f"{self.side}_{self.module_name}Pv{prefix.capitalize()}Offset_MMX", ss=True)
            dm = cmds.createNode('decomposeMatrix', name=f"{self.side}_{self.module_name}Pv{prefix.capitalize()}Offset_DCM", ss=True)
            # cmds.connectAttr(matrix_attr, f'{mm}.matrixIn[0]')
            # cmds.setAttr(f'{mm}.matrixIn[1]', [1, 0, 0, 0,
            #         0, 1, 0, 0,
            #         0, 0, 1, 0,
            #         0, 0, 0, 1], type='matrix')
            cmds.connectAttr(matrix_attr, f'{dm}.inputMatrix')
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

        # compose_node = cmds.createNode('composeMatrix', name=f"{self.side}_{self.module_name}PvCompose_CMT", ss=True)
        # cmds.connectAttr(pole_pos, f'{compose_node}.inputTranslate')

        fourByFour = cmds.createNode('fourByFourMatrix', name=f"{self.side}_{self.module_name}PvFourByFour_FBM", ss=True)
        cmds.connectAttr(f"{pole_pos}.output3Dx", f'{fourByFour}.in30')
        cmds.connectAttr(f"{pole_pos}.output3Dy", f'{fourByFour}.in31')
        cmds.connectAttr(f"{pole_pos}.output3Dz", f'{fourByFour}.in32')

        aim_matrix = cmds.createNode('aimMatrix', name=f"{self.side}_{self.module_name}PvAim_AMX", ss=True)
        cmds.setAttr(f'{aim_matrix}.primaryInputAxis', 0, 0, 1, type='double3')
        cmds.setAttr(f'{aim_matrix}.secondaryInputAxis', 1, 0, 0, type='double3')
        cmds.setAttr(f'{aim_matrix}.secondaryTargetVector', 1, 0, 0, type='double3')
        cmds.setAttr(f'{aim_matrix}.primaryMode', 1)
        cmds.setAttr(f'{aim_matrix}.secondaryMode', 2)
        cmds.connectAttr(f'{fourByFour}.output', f'{aim_matrix}.inputMatrix')
        cmds.connectAttr(f'{m2_attr}', f"{aim_matrix}.primaryTargetMatrix")
        cmds.connectAttr(f'{m2_attr}', f'{aim_matrix}.secondaryTargetMatrix')

        blend_matrix = cmds.createNode('blendMatrix', name=f"{self.side}_{self.module_name}PvBlend_BLM", ss=True)
        cmds.connectAttr(f'{fourByFour}.output', f'{blend_matrix}.inputMatrix')
        cmds.connectAttr(f'{aim_matrix}.outputMatrix', f'{blend_matrix}.target[0].targetMatrix')

        return blend_matrix

    def ik_rig(self):
        """
        Create IK chain for the limb.
        This function creates an inverse kinematics chain for the limb, including controllers and constraints.
        """
        self.ik_controllers = cmds.createNode("transform", name=f"{self.side}_{self.module_name}IkControllers_GRP", parent=self.individual_controllers_grp, ss=True)

        self.root_ik_ctl, self.root_ik_ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}RootIk",
            suffixes=["GRP", "ANM"],
            lock=["sx","sz","sy","visibility"],
            ro=True,
            parent=self.ik_controllers
        )
        self.pv_ik_ctl, self.pv_ik_ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}PV",
            suffixes=["GRP", "ANM"],
            lock=["rx", "ry", "rz", "sx","sz","sy","visibility"],
            ro=False,
            parent=self.ik_controllers

        )
        self.hand_ik_ctl, self.hand_ik_ctl_grp = controller_creator(
            name=f"{self.side}_{self.module_name}Ik",
            suffixes=["GRP", "ANM"],
            lock=["visibility"],
            ro=True,
            parent=self.ik_controllers

        )

        cmds.connectAttr(self.guides_matrix[2] + ".outputMatrix", f"{self.hand_ik_ctl_grp[0]}.offsetParentMatrix")

        cmds.addAttr(self.pv_ik_ctl, shortName="extraAttr", niceName="Extra Attributes  ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.pv_ik_ctl+".extraAttr", channelBox=True, lock=True)
        cmds.addAttr(self.pv_ik_ctl, shortName="pvOrientation", niceName="Pv Orientation",defaultValue=0, minValue=0, maxValue=1, keyable=True)

        cmds.addAttr(self.pv_ik_ctl, shortName="poleVectorPinning", niceName="Pole Vector Pinning ———", enumName="———",attributeType="enum", keyable=True)
        cmds.setAttr(self.pv_ik_ctl+".poleVectorPinning", channelBox=True, lock=True)
        cmds.addAttr(self.pv_ik_ctl, shortName="pin", niceName="Pin",minValue=0,maxValue=1,defaultValue=0, keyable=True)
        
        cmds.connectAttr(f"{self.guides_matrix[0]}.outputMatrix", f"{self.root_ik_ctl_grp[0]}.offsetParentMatrix")      

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

        pv_pos = self.create_matrix_pole_vector(
            f"{self.guides_matrix[0]}.outputMatrix",
            f"{self.guides_matrix[1]}.outputMatrix",
            f"{self.guides_matrix[2]}.outputMatrix",
            name=f"{self.side}_{self.module_name}PV"
        )

        cmds.connectAttr(f"{self.pv_ik_ctl}.pvOrientation", f"{pv_pos}.target[0].weight")
        cmds.connectAttr(f"{pv_pos}.outputMatrix", f"{self.pv_ik_ctl_grp[0]}.offsetParentMatrix")

        self.distance_between_output = []
        for i, (first, second) in enumerate(zip([self.guides[0], self.guides[1], self.root_ik_ctl], [self.guides[1], self.guides[2], self.hand_ik_ctl])):
            distance = cmds.createNode("distanceBetween", name=f"{self.side}_{self.module_name}IkDistance0{i+1}_DB")
            cmds.connectAttr(f"{first}.worldMatrix[0]", f"{distance}.inMatrix1")
            cmds.connectAttr(f"{second}.worldMatrix[0]", f"{distance}.inMatrix2")
            self.distance_between_output.append(f"{distance}.distance")

        sum_distance = cmds.createNode("sum", name=f"{self.side}_{self.module_name}InitialLenght_SUM")
        cmds.connectAttr(self.distance_between_output[0], f"{sum_distance}.input[0]")
        cmds.connectAttr(self.distance_between_output[1], f"{sum_distance}.input[1]")

        divide = cmds.createNode("divide", name=f"{self.side}_{self.module_name}InitialLenght_DIV", ss=True)
        cmds.connectAttr(f"{self.distance_between_output[2]}", f"{divide}.input1")
        cmds.connectAttr(f"{sum_distance}.output", f"{divide}.input2")

        max = cmds.createNode("max", name=f"{self.side}_{self.module_name}InitialLenght_MAX")
        cmds.connectAttr(f"{divide}.output", f"{max}.input[0]")
        cmds.setAttr(f"{max}.input[1]", 1)  ############### QUIZAS SE HA DE PONER UN FLOATCONSTANT PROBAR SI GUARDA EL VALOR

        self.stretch_distances = cmds.createNode("condition", name=f"{self.side}_{self.module_name}StretchLenght_COND")
        cmds.connectAttr(f"{self.hand_ik_ctl}.stretch", f"{self.stretch_distances}.firstTerm")
        cmds.setAttr(f"{self.stretch_distances}.secondTerm", 1)
        cmds.setAttr(f"{self.stretch_distances}.operation", 0)

        for i, (attr, value) in enumerate(zip(["upperLengthMult", "lowerLengthMult"], ["R", "G"])):
            multiply = cmds.createNode("multiply", name=f"{self.side}_{self.module_name}StretchLenght0{i}_MULT")
            cmds.connectAttr(f"{self.distance_between_output[i]}", f"{multiply}.input[0]")
            cmds.connectAttr(f"{max}.output", f"{multiply}.input[1]")
            cmds.connectAttr(f"{self.hand_ik_ctl}.{attr}", f"{multiply}.input[2]")

            cmds.connectAttr(f"{self.distance_between_output[i]}", f"{self.stretch_distances}.colorIfFalse{value}")
            cmds.connectAttr(f"{multiply}.output", f"{self.stretch_distances}.colorIfTrue{value}")

        # --- CUSTOM SOLVER --- #

        power_mults = []
        for i, distance in enumerate([self.distance_between_output[-1], f"{self.stretch_distances}.outColorR", f"{self.stretch_distances}.outColorG"]):
            name = distance.split(".")[0]
            name = "_".join(name.split("_")[:2])
            multiply = cmds.createNode("multiply", name=f"{name}Power0{i+1}_MULT")
            cmds.connectAttr(f"{distance}", f"{multiply}.input[0]")
            cmds.connectAttr(f"{distance}", f"{multiply}.input[1]")
            power_mults.append(multiply)
        
        c = self.distance_between_output[-1]
        a = f"{self.stretch_distances}.outColorR"
        b = f"{self.stretch_distances}.outColorG"

        # a2 + c2 -b2
        sum = cmds.createNode("sum", name=f"{self.side}_{self.module_name}UpperArmCustomSolver_SUM")
        cmds.connectAttr(f"{power_mults[1]}.output", f"{sum}.input[0]")
        cmds.connectAttr(f"{power_mults[0]}.output", f"{sum}.input[1]")

        subtract = cmds.createNode("subtract", name=f"{self.side}_{self.module_name}UpperArmCustomSolver_SUB")
        cmds.connectAttr(f"{sum}.output", f"{subtract}.input1")
        cmds.connectAttr(f"{power_mults[2]}.output", f"{subtract}.input2")

        # 2ac
        multiply = cmds.createNode("multiply", name=f"{self.side}_{self.module_name}UpperArmCustomSolver_MULT")
        cmds.setAttr(f"{multiply}.input[0]", 2)
        cmds.connectAttr(f"{a}", f"{multiply}.input[1]")
        cmds.connectAttr(f"{c}", f"{multiply}.input[2]")

        #complete formula
        divide = cmds.createNode("divide", name=f"{self.side}_{self.module_name}UpperArmCustomSolver_DIV", ss=True)
        cmds.connectAttr(f"{subtract}.output", f"{divide}.input1")
        cmds.connectAttr(f"{multiply}.output", f"{divide}.input2")

        upper_arm_acos = cmds.createNode("acos", name=f"{self.side}_{self.module_name}UpperArmCustomSolver_ACOS")
        cmds.connectAttr(f"{divide}.output", f"{upper_arm_acos}.input")

        # a2 + b2 - c2
        sum = cmds.createNode("sum", name=f"{self.side}_{self.module_name}LowerArmCustomSolver_SUM")
        cmds.connectAttr(f"{power_mults[1]}.output", f"{sum}.input[0]")
        cmds.connectAttr(f"{power_mults[2]}.output", f"{sum}.input[1]")

        subtract = cmds.createNode("subtract", name=f"{self.side}_{self.module_name}LowerArmCustomSolver_SUB")
        cmds.connectAttr(f"{sum}.output", f"{subtract}.input1")
        cmds.connectAttr(f"{power_mults[0]}.output", f"{subtract}.input2")

        # 2ab
        multiply = cmds.createNode("multiply", name=f"{self.side}_{self.module_name}LowerArmCustomSolver_MULT")
        cmds.setAttr(f"{multiply}.input[0]", 2)
        cmds.connectAttr(f"{a}", f"{multiply}.input[1]")
        cmds.connectAttr(f"{b}", f"{multiply}.input[2]")

        #complete formula
        divide = cmds.createNode("divide", name=f"{self.side}_{self.module_name}LowerArmCustomSolver_DIV", ss=True)
        cmds.connectAttr(f"{subtract}.output", f"{divide}.input1")
        cmds.connectAttr(f"{multiply}.output", f"{divide}.input2")

        acos = cmds.createNode("acos", name=f"{self.side}_{self.module_name}LowerArmCustomSolver_ACOS")
        cmds.connectAttr(f"{divide}.output", f"{acos}.input")

        subtract = cmds.createNode("subtract", name=f"{self.side}_{self.module_name}LowerArmCustomSolverFlip_SUB")
        cmds.connectAttr(f"{acos}.output", f"{subtract}.input1")
        cmds.setAttr(f"{subtract}.input2", 180)

        # lower_arm_negate = cmds.createNode("negate", name=f"{self.side}_{self.module_name}LowerArmCustomSolverFlip_NEGATE")
        # cmds.connectAttr(f"{subtract}.output", f"{lower_arm_negate}.input")

        # --- Aligns --- #

        upper_arm_ik_aim_matrix = cmds.createNode("aimMatrix", name=f"{self.side}_{self.module_name}UpperArmIk_AIM", ss=True)
        cmds.connectAttr(f"{self.hand_ik_ctl}.worldMatrix", f"{upper_arm_ik_aim_matrix}.primaryTargetMatrix")
        cmds.connectAttr(f"{self.pv_ik_ctl}.worldMatrix", f"{upper_arm_ik_aim_matrix}.secondaryTargetMatrix")
        cmds.connectAttr(f"{self.root_ik_ctl}.worldMatrix", f"{upper_arm_ik_aim_matrix}.inputMatrix")

        cmds.setAttr(upper_arm_ik_aim_matrix + ".secondaryInputAxis", *(0, 1, 0), type="double3")
        cmds.setAttr(upper_arm_ik_aim_matrix + ".secondaryMode", 1)
        # cmds.setAttr(upper_arm_ik_aim_matrix + ".secondaryTargetVector", *(0, 1, 0), type="double3")
        
        joint = cmds.createNode("joint", name=f"{self.side}_{self.module_name}UpperArmIk_JNT")
        joint2 = cmds.createNode("joint", name=f"{self.side}_{self.module_name}UpperArmIk_JNT2", parent=joint)
        joint3 = cmds.createNode("joint", name=f"{self.side}_{self.module_name}LowerArmIk_JNT", parent=joint2)

        cmds.connectAttr(f"{upper_arm_ik_aim_matrix}.outputMatrix", f"{joint}.offsetParentMatrix")
        cmds.connectAttr(f"{upper_arm_acos}.output", f"{joint}.rz")

        cmds.connectAttr(f"{self.stretch_distances}.outColorR", f"{joint2}.tx")
        cmds.connectAttr(f"{self.stretch_distances}.outColorG", f"{joint3}.tx")
        cmds.connectAttr(f"{subtract}.output", f"{joint2}.rz")

class ArmModule(LimbModule):
    """
    Class for moditifying limb module specific to arms.
    Inherits from LimbModule.
    """

    def __init__(self, guide_name):
        side = guide_name.split("_")[0]

        super().__init__(side)

        self.module_name = "arm"

        self.guides = guide_import(guide_name, all_descendents=True, path=None)
        if cmds.attributeQuery("moduleName", node=self.guides[0], exists=True):
            self.enum_str = cmds.attributeQuery("moduleName", node=self.guides[0], listEnum=True)[0]

        self.scapula_guide = self.guides[0]

        self.guides = self.guides[1:]

        self.oriented_ik = False

        # Arm-specific setup
        if self.side == "L":
            self.primary_aim = (1, 0, 0)
            self.secondary_aim = (0, -1, 0)
            self.prefered_angle = (0, -1, 0)

        elif self.side == "R":
            self.primary_aim = (-1, 0, 0)
            self.secondary_aim = (0, 0, -1)
            self.prefered_angle = (0, -1, 0)

        self.default_ik = 1

    def make(self):
        
        super().make()

        self.data_exporter.append_data(
            f"{self.side}_{self.module_name}Module",
            {
                "skinning_transform": self.skinnging_grp,
                "fk_ctl": self.fk_ctls,
                "pv_ctl": self.pv_ik_ctl,   
                "root_ctl": self.root_ik_ctl,
                "end_ik": self.hand_ik_ctl,
            }
        )

cmds.file(new=True, force=True)

core.DataManager.set_guide_data("D:/git/maya/biped_autorig/guides/moana_01.guides")
core.DataManager.set_ctls_data("D:/git/maya/biped_autorig/curves/elephant_02.ctls")

basic_structure.create_basic_structure(asset_name="moana_02")
a = ArmModule("L_clavicle_GUIDE").make()