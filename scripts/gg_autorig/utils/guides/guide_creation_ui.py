import maya.cmds as cmds
from importlib import reload
import json

from gg_autorig.utils import core
import re
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
        i = 1
        while cmds.objExists(transform_name):
            if not re.search(r"\d+_GUIDE$", transform_name):
                transform_name = transform_name.replace("_GUIDE", f"0{i}_GUIDE")
            else:
                transform_name = transform_name.replace(f"{i-1}_GUIDE", f"{i}_GUIDE")
            i += 1
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
            if "scale" in attr:
                try:
                    cmds.connectAttr(f"{self.guides_trn}.guideScale", f"{ctl}.{attr}", force=True)
                except:
                    pass
            cmds.setAttr(f"{ctl}.{attr}", keyable=False, channelBox=False, lock=True)

        return ctl

    def create_guides(self, guides_trn, buffers_trn):
        self.guides_trn = guides_trn
        self.buffers_trn = buffers_trn

        for side in self.sides:
            color = {"L": 6, "R": 13}.get(side, 17)
            self.guides = []
            for i, (joint_name, position) in enumerate(self.position_data.items()):
                temp_pos = cmds.createNode("transform", name=f"{side}_{joint_name}_temp")
                type = "joint"
                cmds.setAttr(temp_pos + ".translate", position[0], position[1], position[2])

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

                if i == 0:
                    if hasattr(self, "twist_joints"):
                        attr_name = "jointTwist"
                        cmds.addAttr(guide, longName=attr_name, attributeType="float", defaultValue=self.twist_joints, keyable=False)
                        cmds.setAttr(f"{guide}.{attr_name}", self.twist_joints)

                    if hasattr(self, "type"):
                        enum_name = "type"
                        cmds.addAttr(guide, longName=enum_name, attributeType="enum", enumName="biped:quadruped", keyable=False)
                        cmds.setAttr(f"{guide}.{enum_name}", 0 if self.type == "biped" else 1)

                    cmds.addAttr(guide, longName="moduleName", attributeType="enum", enumName=self.limb_name, keyable=False)




                cmds.delete(temp_pos)
                self.guides.append(guide)
            enum_name = ":".join(self.guides)
            cmds.addAttr(self.guides[0], longName="guide_name", attributeType="enum", enumName=enum_name, keyable=False)

            meta = []

            for i in range(len(self.guides) - 1):
                if "Settings" in self.guides[i+1] or "localHip" in self.guides[i+1]:
                    continue
                if "metacarpal" in self.guides[i] or "Metacarpal" in self.guides[i]:
                    print("meta feo")
                    if cmds.listRelatives(self.guides[i], parent=True) != [self.guides[0]]:
                        cmds.parent(self.guides[i], self.guides[0])
                    curve = cmds.curve(d=1, p=[(1, 0, 0), (2, 0, 0)], n=f"{self.guides[i]}_to_{self.guides[0]}_CRV")
                    dcmp = cmds.createNode("decomposeMatrix", name=f"{self.guides[i]}_to_{self.guides[0]}{i}_DCM", ss=True)
                    dcmp02 = cmds.createNode("decomposeMatrix", name=f"{self.guides[i]}_to_{self.guides[0]}{i+1}_DCM", ss=True)
                    cmds.connectAttr(self.guides[i] + ".worldMatrix[0]", dcmp + ".inputMatrix")
                    cmds.connectAttr(self.guides[0] + ".worldMatrix[0]", dcmp02 + ".inputMatrix")
                    cmds.connectAttr(dcmp + ".outputTranslate", curve + ".controlPoints[0]")
                    cmds.connectAttr(dcmp02 + ".outputTranslate", curve + ".controlPoints[1]")
                    cmds.parent(curve, self.buffers_trn)
                    cmds.setAttr(curve + ".overrideEnabled", 1)
                    cmds.setAttr(curve + ".overrideDisplayType", 1)

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

        cmds.select(self.guides[0])
        return self.guides

def get_data(name, file_name=None):
    if not file_name or file_name == "_":
        file_name = "body_template_"

    # final_path = core.init_template_file(ext=".guides", export=False)
    final_path = core.init_template_file(ext=".guides", export=False)

    try:
        with open(final_path, "r") as infile:
            guides_data = json.load(infile)
    except Exception as e:
        return [0,0,0]

    for template_name, guides in guides_data.items():
        if not isinstance(guides, dict):
            continue
        for guide_name, guide_info in guides.items():
            if name in guide_name:
                return guide_info.get("worldPosition")
    return [0,0,0]



class ArmGuideCreation(GuideCreation):
    """
    Guide creation for arms.
    """
    def __init__(self, side = "L", twist_joints=5):
        self.sides = side
        self.twist_joints = twist_joints
        self.limb_name = "arm"
        self.aim_name = "shoulder"
        self.aim_offset = 0
        self.position_data = {
            "clavicle": get_data(f"{self.sides}_clavicle"),
            "shoulder": get_data(f"{self.sides}_shoulder"),
            "elbow": get_data(f"{self.sides}_elbow"),
            "wrist": get_data(f"{self.sides}_wrist"),
            "armSettings": get_data(f"{self.sides}_armSettings"),
        }

class LegGuideCreation(GuideCreation):
    """
    Guide creation for legs.
    """
    def __init__(self, side = "L", twist_joints=5):
        self.sides = side
        self.twist_joints = twist_joints
        self.limb_name = "leg"
        self.aim_name = "hip"
        self.aim_offset = -1
        self.position_data = {
            "hip": get_data(f"{self.sides}_hip"),
            "knee": get_data(f"{self.sides}_knee"),
            "ankle": get_data(f"{self.sides}_ankle"),
            "ball": get_data(f"{self.sides}_ball"),
            "tip": get_data(f"{self.sides}_tip"),
            "legSettings": get_data(f"{self.sides}_legSettings"),
        }

class FrontLegGuideCreation(GuideCreation):
    """
    Guide creation for front legs.
    """
    def __init__(self, side = "L", twist_joints=5):
        self.sides = side
        self.twist_joints = twist_joints
        self.limb_name = "frontLeg"
        self.aim_name = "scapula"
        self.aim_offset = -1
        self.position_data = {
        "scapula": get_data(f"{self.sides}_scapula"),
        "shoulder": get_data(f"{self.sides}_shoulder"),
        "frontKnee": get_data(f"{self.sides}_frontKnee"),
        "frontAnkle": get_data(f"{self.sides}_frontAnkle"),
        "frontFoot": get_data(f"{self.sides}_frontFoot"),
        "frontToe": get_data(f"{self.sides}_frontToe"),
        "frontLegSettings": get_data(f"{self.sides}_frontLegSettings"),
    }

class BackLegGuideCreation(GuideCreation):
    """
    Guide creation for back legs.
    """
    def __init__(self, side = "L", twist_joints=5):
        self.sides = side
        self.twist_joints = twist_joints
        self.limb_name = "backLeg"
        self.aim_name = "hip"
        self.aim_offset = -1
        self.position_data = {
        "hip": get_data(f"{self.sides}_hip"),
        "backKnee": get_data(f"{self.sides}_backKnee"),
        "backAnkle": get_data(f"{self.sides}_backAnkle"),
        "backFoot": get_data(f"{self.sides}_backFoot"),
        "backToe": get_data(f"{self.sides}_backToe"),
        "backLegSettings": get_data(f"{self.sides}_backLegSettings"),
    }

class SpineGuideCreation(GuideCreation):
    """
    Guide creation for spine.
    """
    def __init__(self, side = "C", twist_joints=5,type="biped"):
        self.sides = side
        self.twist_joints = twist_joints
        self.type = type
        self.limb_name = "spine"
        self.aim_name = None
        self.position_data = {
        "spine01": get_data(f"{self.sides}_spine01"),
        "spine02": get_data(f"{self.sides}_spine02"),
        "localHip": get_data(f"{self.sides}_localHip"),
    }

class NeckGuideCreation(GuideCreation):
    """
    Guide creation for neck.
    """
    def __init__(self, side = "C", twist_joints=5, type=0):
        self.sides = side
        self.type = type
        self.twist_joints = twist_joints
        self.limb_name = "neck"
        self.aim_name = None
        self.position_data = {
            "neck": get_data(f"{self.sides}_neck"),
            "head": get_data(f"{self.sides}_head"),
        }

def number_to_ordinal_word(n):
    base_ordinal = {
        1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
        6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
        11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
        15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
        19: 'nineteenth'
    }
    tens = {
        20: 'twentieth', 30: 'thirtieth', 40: 'fortieth',
        50: 'fiftieth', 60: 'sixtieth', 70: 'seventieth',
        80: 'eightieth', 90: 'ninetieth'
    }
    tens_prefix = {
        20: 'twenty', 30: 'thirty', 40: 'forty', 50: 'fifty',
        60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninety'
    }
    if n <= 19:
        return base_ordinal[n]
    elif n in tens:
        return tens[n]
    elif n < 100:
        ten = (n // 10) * 10
        unit = n % 10
        return tens_prefix[ten] + "-" + base_ordinal[unit]
    else:
        return str(n)


class HandGuideCreation(GuideCreation):
    """
    Guide creation for hands.
    """
    def __init__(self, side = "L", controller_number = 5):
        self.sides = side
        self.limb_name = "hand"
        self.aim_name = None
        self.aim_offset = 1
        if controller_number == 5:
            self.position_data = {
                "hand": get_data(f"{self.sides}_hand"),
                "metacarpalIndex": get_data(f"{self.sides}_metacarpalIndex"),
                "index01": get_data(f"{self.sides}_index01"),
                "index02": get_data(f"{self.sides}_index02"),
                "index03": get_data(f"{self.sides}_index03"),
                "indexEnd": get_data(f"{self.sides}_indexEnd"),
                "metacarpalMiddle": get_data(f"{self.sides}_metacarpalMiddle"),
                "middle01": get_data(f"{self.sides}_middle01"),
                "middle02": get_data(f"{self.sides}_middle02"),
                "middle03": get_data(f"{self.sides}_middle03"),
                "middleEnd": get_data(f"{self.sides}_middleEnd"),
                "metacarpalRing": get_data(f"{self.sides}_metacarpalRing"),
                "ring01": get_data(f"{self.sides}_ring01"),
                "ring02": get_data(f"{self.sides}_ring02"),
                "ring03": get_data(f"{self.sides}_ring03"),
                "ringEnd": get_data(f"{self.sides}_ringEnd"),
                "metacarpalPinky": get_data(f"{self.sides}_metacarpalPinky"),
                "pinky01": get_data(f"{self.sides}_pinky01"),
                "pinky02": get_data(f"{self.sides}_pinky02"),
                "pinky03": get_data(f"{self.sides}_pinky03"),
                "pinkyEnd": get_data(f"{self.sides}_pinkyEnd"),
                "metacarpalThumb": get_data(f"{self.sides}_metacarpalThumb"),
                "thumb01": get_data(f"{self.sides}_thumb01"),
                "thumb02": get_data(f"{self.sides}_thumb02"),
                "thumbEnd": get_data(f"{self.sides}_thumbEnd"),
            }
        else:
            self.position_data = {
                "hand": get_data(f"{self.sides}_hand"),
            }
            for item in range(int(controller_number)):
                name = number_to_ordinal_word(item + 1)
                if name == "first":
                    self.position_data.update({
                        f"{name}Metacarpal": get_data(f"{self.sides}_{name}Metacarpal"),
                        f"{name}Finger01": get_data(f"{self.sides}_{name}Finger01"),
                        f"{name}Finger02": get_data(f"{self.sides}_{name}Finger02"),
                        f"{name}FingerEnd": get_data(f"{self.sides}_{name}FingerEnd"),
                    })
                else:
                    self.position_data.update({
                        f"{name}Metacarpal": get_data(f"{self.sides}_{name}Metacarpal"),
                        f"{name}Finger01": get_data(f"{self.sides}_{name}Finger01"),
                        f"{name}Finger02": get_data(f"{self.sides}_{name}Finger02"),
                        f"{name}Finger03": get_data(f"{self.sides}_{name}Finger03"),
                        f"{name}FingerEnd": get_data(f"{self.sides}_{name}FingerEnd"),
                    })

class FootGuideCreation(GuideCreation):
    """
    Guide creation for feet.
    """
    def __init__(self, side = "L", limb_name="foot"):
        self.sides = side
        self.reverse_foot_name = limb_name
        self.limb_name = "foot"
        self.aim_name = None
        self.aim_offset = 0
        ctl = "" if self.reverse_foot_name == "foot" else self.reverse_foot_name
        first_b_letter = "b" if ctl == "" else "B"
        first_h_letter = "h" if ctl == "" else "H"
        self.position_data = {
        f"{ctl}{first_b_letter}ankOut": get_data(f"{self.sides}_{ctl}{first_b_letter}ankOut"),
        f"{ctl}{first_b_letter}ankIn": get_data(f"{self.sides}_{ctl}{first_b_letter}ankIn"),
        f"{ctl}{first_h_letter}eel": get_data(f"{self.sides}_{ctl}{first_h_letter}eel"),
    }
        
class VariableFK(GuideCreation):
    """
    Guide creation for variable FK.
    """
    limb_name = "variableFK"
    aim_name = None
    aim_offset = 0

    def __init__(self, quantity=5, sides=["L", "R"], prefix="trunk"):
        self.sides = sides
        self.quantity = quantity
        self.prefix = prefix

        zero_value = 3 if quantity >= 10 else 2

        self.position_data = {}


        for i in range(self.quantity):

            position_data = {
                f"{self.prefix}VariableFK{str(i+1).zfill(zero_value)}": get_data(f"{self.prefix}VariableFK{str(i+1).zfill(zero_value)}"),
            }
            self.position_data.update(position_data)

class JiggleJoint(GuideCreation):
    """
    Guide creation for jiggle joints.
    """
    sides = ["L", "R"]
    limb_name = "jiggleJoint"
    aim_name = None
    aim_offset = 0

    def __init__(self, prefix="tail"):
        position_data = {
            f"{prefix}JiggleJoint": get_data(f"{prefix}JiggleJoint"),

        }
        self.position_data.update(position_data)

def biped_rebuild_guides():
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

def quadruped_rebuild_guides():
    """
    Rebuilds the guides for a quadruped character in the Maya scene.
    This function creates a new guides group and populates it with guides for front legs, back legs, spine, neck, hands, and feet.
    """

    guides_trn = cmds.createNode("transform", name="guides_GRP", ss=True)
    buffers_trn = cmds.createNode("transform", name="buffers_GRP", ss=True, parent=guides_trn)



    FrontLegGuideCreation().create_guides(guides_trn, buffers_trn)
    BackLegGuideCreation().create_guides(guides_trn, buffers_trn)
    SpineGuideCreation().create_guides(guides_trn, buffers_trn)
    NeckGuideCreation().create_guides(guides_trn, buffers_trn)
    VariableFK(quantity=15, sides=["C"], prefix="trunk").create_guides(guides_trn, buffers_trn)
    VariableFK(quantity=15, sides=["C"], prefix="tail").create_guides(guides_trn, buffers_trn)
    JiggleJoint(quantity=15, sides=["C"], prefix="tail").create_guides(guides_trn, buffers_trn)

def load_guides(path = ""):
    if not path or path == "_":
        path = "body_template_"

    # final_path = core.init_template_file(ext=".guides", export=False, file_name=path)
    final_path = core.init_template_file(ext=".guides", export=False)

    try:
        with open(final_path, "r") as infile:
            guides_data = json.load(infile)

    except Exception as e:
        om.MGlobal.displayError(f"Error loading guides data: {e}")

    # Example: get world position and rotation for "wrist"

    if not cmds.objExists("guides_GRP"):
        guides_trn = cmds.createNode("transform", name="guides_GRP", ss=True)
    else:
        guides_trn = "guides_GRP"
    if not cmds.objExists("buffers_GRP"):
        buffers_trn = cmds.createNode("transform", name="buffers_GRP", ss=True, parent=guides_trn)
    else:
        buffers_trn = "buffers_GRP"
        if cmds.listRelatives(buffers_trn, parent=True) != [guides_trn]:
            cmds.parent(buffers_trn, guides_trn)

    cmds.setAttr(f"{buffers_trn}.hiddenInOutliner ", True)

    for template_name, guides in guides_data.items():
        if not isinstance(guides, dict):
            continue  # ignorar "hierarchy" u otros que no sean diccionarios de guías

        for guide_name, guide_info in guides.items():
            if guide_info.get("moduleName") != "Child":
                if guide_info.get("moduleName") == "arm":
                    ArmGuideCreation(side=guide_name.split("_")[0], twist_joints=guide_info.get("jointTwist")).create_guides(guides_trn, buffers_trn)
                if guide_info.get("moduleName") == "frontLeg":
                    FrontLegGuideCreation(side=guide_name.split("_")[0], twist_joints=guide_info.get("jointTwist")).create_guides(guides_trn, buffers_trn)
                if guide_info.get("moduleName") == "leg":
                    LegGuideCreation(side=guide_name.split("_")[0], twist_joints=guide_info.get("jointTwist")).create_guides(guides_trn, buffers_trn)
                if guide_info.get("moduleName") == "backLeg":
                    BackLegGuideCreation(side=guide_name.split("_")[0], twist_joints=guide_info.get("jointTwist")).create_guides(guides_trn, buffers_trn)
                if guide_info.get("moduleName") == "spine":
                    SpineGuideCreation(side=guide_name.split("_")[0], twist_joints=guide_info.get("jointTwist"), type=guide_info.get("type")).create_guides(guides_trn, buffers_trn)
                if guide_info.get("moduleName") == "neck":
                    NeckGuideCreation(side=guide_name.split("_")[0], twist_joints=guide_info.get("jointTwist"), type=guide_info.get("type")).create_guides(guides_trn, buffers_trn)
                if guide_info.get("moduleName") == "foot":
                    limb_name = guide_name.split("_")[1].split("BankOut")[0]
                    FootGuideCreation(side=guide_name.split("_")[0], limb_name=limb_name).create_guides(guides_trn, buffers_trn)



# biped_rebuild_guides()
# quadruped_rebuild_guides()