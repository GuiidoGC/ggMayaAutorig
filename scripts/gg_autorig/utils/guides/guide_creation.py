import maya.cmds as cmds
import gg_autorig.utils.curve_tool as curve_tool
from gg_autorig.utils.curve_tool import controller_creator   
from gg_autorig.utils.curve_tool import init_template_file  
from importlib import reload
reload(curve_tool)

init_template_file("D:/git/maya/biped_autorig/curves/guides_curves_template.json")
class GuideCreation(object):
    """
    Base class to create guides in the Maya scene.
    Contains shared logic for guide creation.
    """

    position_data = {}
    value = 0

    def create_guides(self, guides_trn, buffers_trn):
        self.guides_trn = guides_trn
        self.buffers_trn = buffers_trn

        


        for side in self.sides:
            self.guides = []
            for joint_name, position in self.position_data.items():
                temp_pos = cmds.createNode("transform", name="temp_pos")
                cmds.setAttr(temp_pos + ".translate", position[0], position[1], position[2])

                if side == "R":
                    cmds.setAttr(temp_pos + ".translateX", position[0] * -1)

                parent = self.guides_trn if not self.guides else self.guides[-1]

                guide = controller_creator(
                    f"{side}_{joint_name}",
                    suffixes=None,
                    mirror=False,
                    parent=parent,
                    match=temp_pos,
                    lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                    ro=True,
                    prefix="GUIDE"
                )
                cmds.delete(temp_pos)
                self.guides.append(guide)


            for i in range(len(self.guides) - 1):
                if not "metacarpal" in self.guides[i+1]:
                    curve = cmds.curve(d=1, p=[(1, 0, 0), (2, 0, 0)], n=f"{self.guides[i]}_to_{self.guides[i + 1]}_CRV")
                    dcmp = cmds.createNode("decomposeMatrix", name=f"{self.guides[i]}_to_{self.guides[i + 1]}{i}_DCM", ss=True)
                    dcmp02 = cmds.createNode("decomposeMatrix", name=f"{self.guides[i]}_to_{self.guides[i + 1]}{i+1}_DCM", ss=True)
                    cmds.connectAttr(self.guides[i] + ".worldMatrix[0]", dcmp + ".inputMatrix")
                    cmds.connectAttr(self.guides[i + 1] + ".worldMatrix[0]", dcmp02 + ".inputMatrix")
                    cmds.connectAttr(dcmp + ".outputTranslate", curve + ".controlPoints[0]")
                    cmds.connectAttr(dcmp02 + ".outputTranslate", curve + ".controlPoints[1]")
                    cmds.parent(curve, self.buffers_trn)
                    cmds.setAttr(curve + ".overrideEnabled", 1)
                    cmds.setAttr(curve + ".overrideDisplayType", 1)
                if "metacarpal" in self.guides[i]:
                    if cmds.listRelatives(self.guides[i], parent=True) != [self.guides_trn]:
                        cmds.parent(self.guides[i], self.guides_trn)
                    


            if self.aim_name:
                arrrow_buffer = controller_creator(
                    f"{side}_{self.limb_name}Buffer",
                    suffixes=None,
                    mirror=False,
                    parent=self.buffers_trn,
                    match=None,
                    lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                    ro=True,
                    prefix="GUIDE"
                )
                cmds.setAttr(arrrow_buffer + ".overrideEnabled", 1)
                cmds.setAttr(arrrow_buffer + ".overrideDisplayType", 2)

                aimMatrix = cmds.createNode("aimMatrix", name=f"{side}_{self.aim_name}_Aim_AMX", ss=True)
                cmds.setAttr(aimMatrix + ".primaryInputAxis", 1, 0, 0, type="double3")
                cmds.setAttr(aimMatrix + ".secondaryInputAxis", 0, -1, 0, type="double3")
                cmds.setAttr(aimMatrix + ".primaryMode", 1)
                cmds.setAttr(aimMatrix + ".secondaryMode", 1)

                value = self.aim_offset

                cmds.connectAttr(self.guides[1 + value] + ".worldMatrix[0]", aimMatrix + ".inputMatrix")
                cmds.connectAttr(aimMatrix + ".outputMatrix", arrrow_buffer + ".offsetParentMatrix")
                cmds.connectAttr(self.guides[2 + value] + ".worldMatrix[0]", aimMatrix + ".primaryTargetMatrix")
                cmds.connectAttr(self.guides[3 + value] + ".worldMatrix[0]", aimMatrix + ".secondaryTargetMatrix")


class ArmGuideCreation(GuideCreation):
    """
    Guide creation for arms.
    """
    sides = ["L", "R"]
    limb_name = "arm"
    aim_name = "shoulder"
    aim_offset = 0
    position_data = {
        "clavicle": [1, 50, 1],
        "shoulder": [5, 50, 0],
        "elbow": [13, 43, 0],
        "wrist": [19, 38, 0],
    }




class LegGuideCreation(GuideCreation):
    """
    Guide creation for legs.
    """
    sides = ["L", "R"]
    limb_name = "leg"
    aim_name = "hip"
    aim_offset = -1
    position_data = {
        "hip": [3, 32, 0],
        "knee": [3, 17, 0],
        "ankle": [3, 3, -2],
        "ball": [3, 1, 3],
        "tip": [3, 1, 5],
    }


class SpineGuideCreation(GuideCreation):
    """
    Guide creation for spine.
    """
    sides = ["C"]
    limb_name = "spine"
    aim_name = None
    position_data = {
        "spine01": [0, 33, 0],
        "spine02": [0, 44, 0],
    }


class NeckGuideCreation(GuideCreation):
    """
    Guide creation for neck.
    """
    sides = ["C"]
    limb_name = "neck"
    aim_name = None
    position_data = {
        "neck": [0, 51, 0],
        "head": [0, 57, 0],
    }


class HandGuideCreation(GuideCreation):
    """
    Guide creation for hands.
    """
    sides = ["L", "R"]
    limb_name = "hand"
    aim_name = None
    aim_offset = 0
    position_data = {
        "index01": [20.78, 35.76, 1.69],
        "index02": [21.74, 34.74, 1.75],
        "index03": [22.25, 34.25, 1.79],
        "indexEnd": [22.81, 33.62, 1.82],
        "metacarpalMiddle": [19.27, 37.51, 0.75],
        "middle01": [20.91, 35.77, 0.76],
        "middle02": [21.9, 34.71, 0.76],
        "middle03": [22.51, 34.13, 0.76],
        "middleEnd": [23.29, 33.33, 0.76],
        "metacarpalRing": [19.22, 37.48, -0.21],
        "ring01": [20.82, 35.79, -0.22],
        "ring02": [21.73, 34.83, -0.23],
        "ring03": [22.33, 34.2, -0.24],
        "ringEnd": [23.02, 33.46, -0.24],
        "metacarpalPinky": [19.08, 37.32, -0.9],
        "pinky01": [20.59, 35.82, -1.01],
        "pinky02": [21.4, 34.89, -1.06],
        "pinky03": [21.83, 34.43, -1.09],
        "pinkyEnd": [22.47, 33.86, -1.14],
        "metacarpalThumb": [19.2, 37.42, 1.59],
        "thumb01": [18.56, 36.45, 2.1],
        "thumb02": [19.03, 35.45, 2.7],
        "thumbEnd": [19.52, 34.41, 3.31],
    }


class FootGuideCreation(GuideCreation):
    """
    Guide creation for feet.
    """
    sides = ["L", "R"]
    limb_name = "foot"
    aim_name = None
    aim_offset = 0
    position_data = {
        "L_bankOut": [6, 0, 2],
        "L_bankIn": [1, 0, 2],
        "L_heel": [3, 0, -4],
    }



guides_trn = cmds.createNode("transform", name="guides_GRP", ss=True)
buffers_trn = cmds.createNode("transform", name="buffers_GRP", ss=True, parent=guides_trn)


ArmGuideCreation().create_guides(guides_trn, buffers_trn)
LegGuideCreation().create_guides(guides_trn, buffers_trn)
SpineGuideCreation().create_guides(guides_trn, buffers_trn)
NeckGuideCreation().create_guides(guides_trn, buffers_trn)
HandGuideCreation().create_guides(guides_trn, buffers_trn)
FootGuideCreation().create_guides(guides_trn, buffers_trn)
