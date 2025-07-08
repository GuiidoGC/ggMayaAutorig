import maya.cmds as cmds
import gg_autorig.utils.curve_tool as curve_tool
from gg_autorig.utils.curve_tool import controller_creator   
from gg_autorig.utils.curve_tool import init_template_file  
from importlib import reload
import json

from gg_autorig.utils import core
reload(core)



reload(curve_tool)

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

def get_data(name):

    final_path = core.init_template_file(ext=".guides", export=False)

    with open(final_path, "r") as infile:
                guides_data = json.load(infile)

    # Example: get world position and rotation for "wrist"
    for template_name, guides in guides_data.items():
        for guide_name, guide_info in guides.items():
            if name in guide_name:
                world_position = guide_info.get("worldPosition")
                # world_rotation = guide_info.get("worldRotation")
                return world_position #world_rotation
    return None, None



class ArmGuideCreation(GuideCreation):
    """
    Guide creation for arms.
    """
    sides = ["L", "R"]
    limb_name = "arm"
    aim_name = "shoulder"
    aim_offset = 0
    position_data = {
        "clavicle": get_data("clavicle"),
        "shoulder": get_data("shoulder"),
        "elbow": get_data("elbow"),
        "wrist": get_data("wrist"),
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
        "hip": get_data("hip"),
        "knee": get_data("knee"),
        "ankle": get_data("ankle"),
        "ball": get_data("ball"),
        "tip": get_data("tip"),
    }


class SpineGuideCreation(GuideCreation):
    """
    Guide creation for spine.
    """
    sides = ["C"]
    limb_name = "spine"
    aim_name = None
    position_data = {
        "spine01": get_data("spine01"),
        "spine02": get_data("spine02"),
    }


class NeckGuideCreation(GuideCreation):
    """
    Guide creation for neck.
    """
    sides = ["C"]
    limb_name = "neck"
    aim_name = None
    position_data = {
        "neck": get_data("neck"),
        "head": get_data("head"),
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
        "metacarpalIndex": get_data("metacarpalIndex"),
        "index01": get_data("index01"),
        "index02": get_data("index02"),
        "index03": get_data("index03"),
        "indexEnd": get_data("indexEnd"),
        "metacarpalMiddle": get_data("metacarpalMiddle"),
        "middle01": get_data("middle01"),
        "middle02": get_data("middle02"),
        "middle03": get_data("middle03"),
        "middleEnd": get_data("middleEnd"),
        "metacarpalRing": get_data("metacarpalRing"),
        "ring01": get_data("ring01"),
        "ring02": get_data("ring02"),
        "ring03": get_data("ring03"),
        "ringEnd": get_data("ringEnd"),
        "metacarpalPinky": get_data("metacarpalPinky"),
        "pinky01": get_data("pinky01"),
        "pinky02": get_data("pinky02"),
        "pinky03": get_data("pinky03"),
        "pinkyEnd": get_data("pinkyEnd"),
        "metacarpalThumb": get_data("metacarpalThumb"),
        "thumb01": get_data("thumb01"),
        "thumb02": get_data("thumb02"),
        "thumbEnd": get_data("thumbEnd"),
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
        "bankOut": get_data("bankOut"),
        "bankIn": get_data("bankIn"),
        "heel": get_data("heel"),
    }


def rebuild_guides():
    """
    Rebuilds the guides in the Maya scene.
    This function creates a new guides group and populates it with guides for arms, legs, spine, neck, hands, and feet.
    """


    guides_trn = cmds.createNode("transform", name="guides_GRP", ss=True)
    buffers_trn = cmds.createNode("transform", name="buffers_GRP", ss=True, parent=guides_trn)


    ArmGuideCreation().create_guides(guides_trn, buffers_trn)
    LegGuideCreation().create_guides(guides_trn, buffers_trn)
    SpineGuideCreation().create_guides(guides_trn, buffers_trn)
    NeckGuideCreation().create_guides(guides_trn, buffers_trn)
    HandGuideCreation().create_guides(guides_trn, buffers_trn)
    FootGuideCreation().create_guides(guides_trn, buffers_trn)
