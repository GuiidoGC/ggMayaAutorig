import maya.cmds as cmds
from importlib import reload
import json

from gg_autorig.utils import core
reload(core)
import maya.api.OpenMaya as om


class GuideCreation(object):
    """
    Base class to create guides in the Maya scene.
    Contains shared logic for guide creation.
    """

    position_data = {}
    value = 0

    def build_curves_from_template(self, type, transform_name):
        """
        Builds controller curves from a predefined template JSON file.
        If a specific target transform name is provided, it filters the curves to only create those associated with that transform.
        If no target transform name is provided, it creates all curves defined in the template.
        """
            
        curve_data = {
            "joint": {
                "shapes": [
                    {
                        "curve": {
                            "cvs": [
                                [-0.22838263, 8.743786e-17, 0.22838263],
                                [-0.32298181, -1.9776932e-17, 2.0788098e-17],
                                [-0.22838263, -1.1540666e-16, -0.22838263],
                                [-8.1458056e-17, -1.4343274e-16, -0.32298181],
                                [0.22838263, -8.743786e-17, -0.22838263],
                                [0.32298181, 1.9776932e-17, -3.1342143e-17],
                                [0.22838263, 1.1540666e-16, 0.22838263],
                                [-2.0669707e-17, 1.4343274e-16, 0.32298181],
                                [-0.22838263, 8.743786e-17, 0.22838263],
                                [-0.32298181, -1.9776932e-17, 2.0788098e-17],
                                [-0.22838263, -1.1540666e-16, -0.22838263]
                            ],
                            "form": "periodic",
                            "knots": [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                            "degree": 3
                        }
                    },
                    {
                        "curve": {
                            "cvs": [
                                [-1.908927e-20, -0.22838263, 0.22838263],
                                [2.6778678e-17, -0.32298181, 9.250447e-17],
                                [-1.908927e-20, -0.22838263, -0.22838263],
                                [-6.4714622e-17, -8.8459802e-17, -0.32298181],
                                [-1.2941016e-16, 0.22838263, -0.22838263],
                                [-1.5620792e-16, 0.32298181, -1.0305851e-16],
                                [-1.2941016e-16, 0.22838263, 0.22838263],
                                [-6.4714622e-17, 1.1576128e-16, 0.32298181],
                                [-1.908927e-20, -0.22838263, 0.22838263],
                                [2.6778678e-17, -0.32298181, 9.250447e-17],
                                [-1.908927e-20, -0.22838263, -0.22838263]
                            ],
                            "form": "periodic",
                            "knots": [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                            "degree": 3
                        }
                    },
                    {
                        "curve": {
                            "cvs": [
                                [-0.22838263, -0.22838263, -1.2973237e-17],
                                [-0.32298181, -1.9776932e-17, -1.8765766e-17],
                                [-0.22838263, 0.22838263, -1.2973237e-17],
                                [-8.1458056e-17, 0.32298181, 1.011166e-18],
                                [0.22838263, 0.22838263, 1.4995569e-17],
                                [0.32298181, 3.2353309e-17, 2.0788098e-17],
                                [0.22838263, -0.22838263, 1.4995569e-17],
                                [-2.0669707e-17, -0.32298181, 1.011166e-18],
                                [-0.22838263, -0.22838263, -1.2973237e-17],
                                [-0.32298181, -1.9776932e-17, -1.8765766e-17],
                                [-0.22838263, 0.22838263, -1.2973237e-17]
                            ],
                            "form": "periodic",
                            "knots": [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                            "degree": 3
                        }
                    }
                ]
            },
            "arrow": {
                "shapes": [
                    {
                        "curve": {
                            "cvs": [
                                [0.05710937039931652, -0.46208100343651526, 1.2381136152831843e-06],
                                [-0.13243611287906498, -0.43980584749283874, 1.1784288984233384e-06],
                                [-0.2709619403561311, -0.46741316704204877, 1.2524007734001178e-06],
                                [-0.3110801360209462, -0.4997154863303799, 1.3389525706362542e-06],
                                [-0.3125322482823646, -0.5452255108954519, 1.4608934871137462e-06],
                                [-0.3279198465141865, -1.0274752154006066, 2.7530477212710005e-06],
                                [-0.3293719587755938, -1.072985239965675, 2.874988637748483e-06],
                                [-0.2913151372523647, -1.1052875592540063, 2.96154043498462e-06],
                                [-0.1504102897778976, -1.1343047230011487, 3.0392898885329146e-06],
                                [0.040251692463613487, -1.1134394112554025, 2.9833827502445854e-06],
                                [0.9838829618428812, -0.9500234372888587, 2.545521118154057e-06],
                                [1.0820129424698943, -0.8688846951636224, 2.3281155537506556e-06],
                                [1.1222758743474053, -0.7876195094560698, 2.1103711926434997e-06],
                                [1.0843407745637117, -0.7055646343449953, 1.8905109142078366e-06],
                                [0.9885386260305203, -0.623383315651595, 1.6703118390683945e-06],
                                [0.05710937039931652, -0.46208100343651526, 1.2381136152831843e-06]
                            ],
                            "form": "open",
                            "knots": [
                                0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 13.0, 13.0
                            ],
                            "degree": 3
                        }
                    }
                ]
            },
            "settings": {
                "shapes": [
                    {
                        "curve": {
                            "cvs": [
                                [0.27583961709940663, 1.1100465970347986, 2.3349109140730323e-07],
                                [0.2760224292833038, 0.27746594834149785, 2.0823220965254452e-07],
                                [1.1042723272392925, 0.2772831361576038, 8.076698100604056e-07],
                                [1.1043942020285566, -0.2777706296379296, 7.90830555557233e-07],
                                [0.27614430407258217, -0.27758781745403516, 1.9139295514937222e-07],
                                [0.2763271162564531, -1.1101684661473408, 1.6613407339461295e-07],
                                [-0.27583948238085565, -1.1100465913580786, -2.3349099354396076e-07],
                                [-0.27602229456474703, -0.2774659426647736, -2.0823211178920218e-07],
                                [-1.1042721925207435, -0.277283130480879, -8.076697121970679e-07],
                                [-1.1043940673100048, 0.2777706353146552, -7.90830457693897e-07],
                                [-0.27614416935401165, 0.2775878231307607, -1.913928572860296e-07],
                                [-0.27632698153791013, 1.1101684718240596, -1.6613397553127101e-07],
                                [0.27583961709940663, 1.1100465970347986, 2.3349109140730323e-07],
                                [0.27583948238086897, 1.1100465913580817, 2.3349099354396645e-07],
                                [-0.2763271162564669, 1.1101684661473432, -1.6613407339460769e-07],
                                [-0.27632698153791013, 1.1101684718240596, -1.6613397553127101e-07],
                                [-0.2763271162564669, 1.1101684661473432, -1.6613407339460769e-07],
                                [-0.27614430407256974, 0.27758781745404004, -1.9139295514936631e-07],
                                [-1.1043942020285564, 0.2777706296379332, -7.908305555572311e-07],
                                [-1.1043940673100048, 0.2777706353146552, -7.90830457693897e-07],
                                [-1.1042721925207435, -0.277283130480879, -8.076697121970679e-07],
                                [-1.1042723272392956, -0.2772831361575999, -8.076698100604056e-07],
                                [-1.1043942020285564, 0.2777706296379332, -7.908305555572311e-07],
                                [-1.1042723272392956, -0.2772831361575999, -8.076698100604056e-07],
                                [-0.276022429283306, -0.2774659483414943, -2.0823220965253864e-07],
                                [-0.2758396170994102, -1.1100465970348, -2.3349109140729796e-07],
                                [-0.27583948238085565, -1.1100465913580786, -2.3349099354396076e-07],
                                [-0.27602229456474703, -0.2774659426647736, -2.0823211178920218e-07],
                                [-0.276022429283306, -0.2774659483414943, -2.0823220965253864e-07],
                                [-0.2758396170994102, -1.1100465970348, -2.3349109140729796e-07],
                                [0.276326981537907, -1.1101684718240636, 1.6613397553127612e-07],
                                [0.2763271162564531, -1.1101684661473408, 1.6613407339461295e-07],
                                [-0.27583948238085565, -1.1100465913580786, -2.3349099354396076e-07],
                                [-0.2758396170994102, -1.1100465970348, -2.3349109140729796e-07],
                                [0.276326981537907, -1.1101684718240636, 1.6613397553127612e-07],
                                [0.27614416935402675, -0.2775878231307562, 1.9139285728603528e-07],
                                [1.1043940673100092, -0.27777063531465007, 7.908304576938965e-07],
                                [1.1043942020285566, -0.2777706296379296, 7.90830555557233e-07],
                                [0.27614430407258217, -0.27758781745403516, 1.9139295514937222e-07],
                                [0.27614416935402675, -0.2775878231307562, 1.9139285728603528e-07],
                                [1.1043940673100092, -0.27777063531465007, 7.908304576938965e-07],
                                [1.1042721925207433, 0.2772831304808836, 8.076697121970698e-07],
                                [0.27602229456475014, 0.2774659426647772, 2.0823211178920748e-07],
                                [0.2760224292833038, 0.27746594834149785, 2.0823220965254452e-07],
                                [1.1042723272392925, 0.2772831361576038, 8.076698100604056e-07],
                                [1.1042721925207433, 0.2772831304808836, 8.076697121970698e-07],
                                [0.27602229456475014, 0.2774659426647772, 2.0823211178920748e-07],
                                [0.27583948238086897, 1.1100465913580817, 2.3349099354396645e-07],
                                [0.27583961709940663, 1.1100465970347986, 2.3349109140730323e-07],
                                [-0.27632698153791013, 1.1101684718240596, -1.6613397553127101e-07],
                                [-0.2763271162564669, 1.1101684661473432, -1.6613407339460769e-07],
                                [-0.27614430407256974, 0.27758781745404004, -1.9139295514936631e-07],
                                [-0.27614416935401165, 0.2775878231307607, -1.913928572860296e-07],
                                [-1.1043940673100048, 0.2777706353146552, -7.90830457693897e-07],
                                [-1.1043942020285564, 0.2777706296379332, -7.908305555572311e-07]
                            ],
                            "form": "open",
                            "knots": [
                                0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0
                            ],
                            "degree": 1
                        }
                    }
                ]
            }
        }

        created_transforms = []
        type_data = curve_data[type]
        shapes_data = type_data.get("shapes", [])

        dag_modifier = om.MDagModifier()
        transform_obj = dag_modifier.createNode("transform")
        dag_modifier.doIt()
        transform_fn = om.MFnDagNode(transform_obj)
        final_name = transform_fn.setName(transform_name)
        created_transforms.append(final_name)

        created_shapes = []
        for idx, shape_data in enumerate(shapes_data):
            curve_info = shape_data["curve"]
            cvs = curve_info["cvs"]
            degree = curve_info["degree"]
            knots = curve_info["knots"]
            form = curve_info["form"]

            form_flags = {
                "open": om.MFnNurbsCurve.kOpen,
                "closed": om.MFnNurbsCurve.kClosed,
                "periodic": om.MFnNurbsCurve.kPeriodic
            }
            form_flag = form_flags.get(form, om.MFnNurbsCurve.kOpen)

            points = om.MPointArray()
            for pt in cvs:
                points.append(om.MPoint(pt[0], pt[1], pt[2]))

            curve_fn = om.MFnNurbsCurve()
            shape_obj = curve_fn.create(
                points,
                knots,
                degree,
                form_flag,
                False,
                True,
                transform_obj
            )

            shape_fn = om.MFnDagNode(shape_obj)
            shape_fn.setName(f"{type}Shape{idx}")

            fn_dep = om.MFnDependencyNode(shape_obj)
            fn_dep.findPlug('alwaysDrawOnTop', False).setBool(True)

            created_shapes.append(shape_obj)

        return created_transforms


    def controller_creator(self,name, type, parent=None, match=None, color=6):
        """
        Creates a controller with a specific name and offset transforms and returns the controller and the groups.

        Args:
            name (str): Name of the controller.
            suffixes (list): List of suffixes for the groups to be created. Default is ["GRP"].
        """
        lock=["scaleX", "scaleY", "scaleZ", "visibility"]
        prefix="GUIDE"

        ctl = self.build_curves_from_template(type=type, transform_name=f"{name}_{prefix}")[0]

        if not ctl:
            ctl = cmds.circle(name=f"{name}_{prefix}", ch=False)

        if parent:
            cmds.parent(ctl, parent)

        cmds.setAttr(f"{ctl}.overrideEnabled", 1)
        cmds.setAttr(f"{ctl}.overrideColor", color)

        if match:
            if cmds.objExists(match):
                cmds.xform(ctl, ws=True, t=cmds.xform(match, q=True, ws=True, t=True))
                cmds.xform(ctl, ws=True, ro=cmds.xform(match, q=True, ws=True, ro=True))


        for attr in lock:
            cmds.setAttr(f"{ctl}.{attr}", keyable=False, channelBox=False, lock=True)

            return ctl

    def create_guides(self, guides_trn, buffers_trn):
        self.guides_trn = guides_trn
        self.buffers_trn = buffers_trn



        for side in self.sides:
            color = {"L": 6, "R": 13}.get(side, 17)
            self.guides = []
            for joint_name, position in self.position_data.items():
                temp_pos = cmds.createNode("transform", name="temp_pos")
                type = "joint"
                cmds.setAttr(temp_pos + ".translate", position[0], position[1], position[2])

                if side == "R":
                    cmds.setAttr(temp_pos + ".translateX", position[0] * -1)

                parent = self.guides_trn if not self.guides else self.guides[-1]
                if "Settings" in joint_name:
                    parent = self.guides[0]
                    type = "settings"
                
                if "localHip" in joint_name:
                    parent = self.guides_trn
                    

                guide = self.controller_creator(
                    f"{side}_{joint_name}",
                    type=type,
                    parent=parent,
                    match=temp_pos,
                    color=color
                )
                cmds.delete(temp_pos)
                self.guides.append(guide)


            for i in range(len(self.guides) - 1):
                if "Settings" in self.guides[i+1] or "localHip" in self.guides[i+1]:
                    continue
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
                arrrow_buffer = self.controller_creator(
                    f"{side}_{self.limb_name}Buffer",
                    type="arrow",
                    parent=self.buffers_trn,
                    match=None,
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
                return world_position
    return [0,0,0]



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
        "armSettings": get_data("armSettings"),
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
        "legSettings": get_data("legSettings"),
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
        "localHip": get_data("localHips"),
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


# rebuild_guides()