import maya.cmds as cmds
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils import data_export

def condition(main_ctl, vis_trn, value):
    """
    Create a condition node to control the visibility of a transform based on a controller's attribute.

    Args:
        main_ctl (str): The name of the controller whose attribute will be used to control visibility.
        vis_trn (str): The name of the transform whose visibility will be controlled.
        value (int): The value to compare against the controller's attribute.
    """
    con = cmds.createNode("condition", name = f"{vis_trn}_Visibility_CON", ss=True)
    cmds.setAttr(con + ".secondTerm", value)
    cmds.connectAttr(main_ctl, con + ".firstTerm")
    cmds.setAttr(con + ".colorIfTrueR", 1)
    cmds.setAttr(con + ".colorIfFalseR", 0)
    cmds.connectAttr(con + ".outColorR", vis_trn + ".visibility")

def create_basic_structure(asset_name = "assetName"):
    """
    Create a basic structure for a Maya asset, including controllers, rig transforms, and model layers.
    Args:
        asset_name (str): The name of the asset to create the structure for. Default is "assetName".
    """

    folder_structure = {
        asset_name: {
            "controls_GRP": {
                "C_characterNode",
                "C_masterWalk",
                "C_preferences"

            },
            "rig_GRP": {
                "modules_GRP",
                "skel_GRP",
                "geoLayering_GRP",
                "skeletonHirearchy_GRP",
                "guides_GRP",
            },
            "model_GRP": {
                "SKELETON",
                "PROXY",
                "LOD_100",
                "LOD_200"
            },
            "groom_GRP": {},
            "clothSim_GRP": {}
        }
    }

    main_transform = cmds.createNode("transform", name=asset_name, ss=True)

    ctls = []
    secondary_transforms = []
    rig_transforms = []



    for folder, subfolders in folder_structure[asset_name].items():
        secondary_transform = cmds.createNode("transform", name=folder, parent=main_transform, ss=True)
        secondary_transforms.append(secondary_transform)
        subfolders = sorted(list(subfolders))
        for subfolder in subfolders:

            if subfolder.startswith("C_"):

                lock_attrs = ["sx", "sy", "sz", "v"]
                ro=False
                if "preferences" in subfolder:
                    lock_attrs += ["tx", "ty", "tz", "rx", "ry", "rz"]
                    ro= True

                ctl, grp = controller_creator(subfolder, ["GRP", "ANM"], lock=lock_attrs, ro=ro)

                cmds.setAttr(f"{ctl}.overrideEnabled", 1)
                if ctls:
                    cmds.parent(grp[0], ctls[-1])
                else:
                    cmds.parent(grp[0], secondary_transform)  
                ctls.append(ctl)
            else:
                trn = cmds.createNode("transform", name=subfolder, parent=secondary_transform, ss=True)
                rig_transforms.append(trn)

    print(rig_transforms)

    data_exporter = data_export.DataExport()
    data_exporter.append_data("basic_structure", {"modules_GRP": rig_transforms[2],
                                                  "skel_GRP": rig_transforms[3],
                                                  "masterWalk_CTL": ctls[1],
                                                  "guides_GRP": rig_transforms[1],})


    cmds.addAttr(ctls[2], shortName="extraAttributesSep", niceName="EXTRA ATTRIBUTES_____", enumName="_____",attributeType="enum", keyable=False)
    cmds.setAttr(ctls[2]+".extraAttributesSep", channelBox=True)
    cmds.addAttr(ctls[2], shortName="reference", niceName="Reference",attributeType="bool", keyable=False, defaultValue=True)
    cmds.setAttr(ctls[2]+".reference", channelBox=True)

    cmds.addAttr(ctls[2], shortName="showModules", niceName="Show Modules",attributeType="bool", keyable=False, defaultValue=False)
    cmds.addAttr(ctls[2], shortName="showJoints", niceName="Show Joints",attributeType="bool", keyable=False, defaultValue=True)
    cmds.addAttr(ctls[2], shortName="meshLods", niceName="LODS", enumName="SKELETON:PROXY:LOD100:LOD200",attributeType="enum", keyable=False)
    cmds.setAttr(ctls[2]+".showModules", channelBox=True)
    cmds.setAttr(ctls[2]+".showJoints", channelBox=True)
    cmds.setAttr(ctls[2]+".meshLods", channelBox=True)

    cmds.setAttr(secondary_transforms[2]+".overrideDisplayType", 2)
    cmds.connectAttr(ctls[2]+".reference", secondary_transforms[2]+".overrideEnabled")
        
    cmds.addAttr(ctls[1], shortName="extraAttributesSep", niceName="EXTRA ATTRIBUTES_____", enumName="_____",attributeType="enum", keyable=True)
    cmds.addAttr(ctls[1], shortName="globalScale", niceName="Global Scale", minValue=0.001,defaultValue=1, keyable=True)
    cmds.setAttr(ctls[1]+".extraAttributesSep", channelBox=True, lock=True)

    for attr in ["sx", "sy", "sz"]:
        cmds.setAttr(f"{ctls[1]}.{attr}", keyable=False, channelBox=False, lock=False)
        cmds.connectAttr(ctls[1]+".globalScale", ctls[1] + f".{attr}", force=True)

        cmds.setAttr(f"{ctls[1]}.{attr}", keyable=False, channelBox=False, lock=True)

    # Optimize meshLods visibility conditions using a loop
    mesh_lods_indices = [7, 6, 4, 5]
    for value, idx in enumerate(mesh_lods_indices):
        condition(f"{ctls[2]}.meshLods", rig_transforms[idx], value)

    cmds.connectAttr(f"{ctls[2]}.showModules", rig_transforms[1]+ ".visibility")
    cmds.connectAttr(f"{ctls[2]}.showJoints", rig_transforms[2] + ".visibility")

    cmds.select(clear=True)

""""

    SETS WIP


    sets = {         
        f"{asset_name}_RIG_SET": {
            "__EXPORT__SET": {
                "__EXPORT__GEO_SET": {
                    secondary_transforms[4],
                    secondary_transforms[3],
                    secondary_transforms[2],
                },
                "__EXPORT__LOCATORS_SET": {},
                "__EXPORT__SKELETON_HIERARCHY_SET": {
                    rig_transforms[3]
                }

            },
            "CONTROLS_SET": {
                ctls[0],
                ctls[1],
                ctls[2],
            }
        }
    }

    set_node = cmds.sets(name=f"{asset_name}_RIG_SET", empty=True)
    for set_name, contents in sets[f"{asset_name}_RIG_SET"].items():
        secondary_set = cmds.sets(name=set_name, empty=True)
        cmds.sets(secondary_set, add=set_node)
        for item, inside in contents.items():
            print(item)
            print(inside)
            if item == "__EXPORT__SET":
                export_set = cmds.sets(name=item, empty=True)
                cmds.sets(export_set, add=secondary_set)

            else:
                cmds.sets(item, add=secondary_set)

         
"""



