

# Tools / utils import
from gg_autorig.utils import basic_structure
from gg_autorig.utils import data_export
from gg_autorig.utils import core
# from gg_autorig.utils.guides import guides_manager

# Rig modules import
from gg_autorig.autorig.ui import limb_module as lbm
from gg_autorig.autorig.ui import spine_module_quadruped as spm_quad
from gg_autorig.autorig.ui import spine_module_biped as spm_bip
from gg_autorig.autorig.ui import neck_module_quadruped as nck_quad
from gg_autorig.autorig.ui import neck_module_biped as nck_bip
from gg_autorig.autorig.ui import skeleton_hierarchy as skh
from gg_autorig.autorig.ui import variable_fk as vfk
from gg_autorig.utils import space_switch as ss
from gg_autorig.autorig.ui import hand_module as han

# Python libraries import
import maya.cmds as cmds
from importlib import reload
import json
import maya.api.OpenMaya as om

reload(basic_structure)
reload(core)
reload(data_export)
reload(lbm)
reload(spm_quad)
reload(spm_bip)
reload(nck_quad)
reload(nck_bip)
reload(ss)
reload(vfk)
reload(skh)
reload(han)

def rename_ctl_shapes():
    """
    Rename all shapes in the scene to follow a specific naming convention.
    This function finds all nurbsCurve shapes in the scene, retrieves their parent transform, and renames the shape to match the parent's name with "Shape" appended.
    """
    
    obj = cmds.ls(type="nurbsCurve")

    for shapes in obj:
        parentName = cmds.listRelatives(shapes, parent=True)[0]
        cmds.rename(shapes, f"{parentName}Shape")

def joint_label():
    """
    Set attributes for all joints in the scene to label them according to their side and type.
    This function iterates through all joints, checks their names for side indicators (L_, R_, C_), and sets the 'side' and 'type' attributes accordingly.
    """

    for jnt in cmds.ls(type="joint"):
        if "L_" in jnt:
            cmds.setAttr(jnt + ".side", 1)
        if "R_" in jnt:
            cmds.setAttr(jnt + ".side", 2)
        if "C_" in jnt:
            cmds.setAttr(jnt + ".side", 0)
        cmds.setAttr(jnt + ".type", 18)
        cmds.setAttr(jnt + ".otherType", jnt.split("_")[1], type= "string")

def make(asset_name="dragon"):
    """
    Build a complete dragon rig in Maya by creating basic structure, modules, and setting up space switching for controllers.
    This function initializes various modules, creates the basic structure, and sets up controllers and constraints for the rig.
    It also sets the radius for all joints and displays a completion message.
    """   

    data_exporter = data_export.DataExport()
    data_exporter.new_build()
    if not asset_name:
        asset_name = "asset"
    basic_structure.create_basic_structure(asset_name=asset_name)

    final_path = core.init_template_file(ext=".guides", export=False)

    try:
        with open(final_path, "r") as infile:
            guides_data = json.load(infile)

    except Exception as e:
        om.MGlobal.displayError(f"Error loading guides data: {e}")

    for template_name, guides in guides_data.items():
        if not isinstance(guides, dict):
            continue

        for guide_name, guide_info in guides.items():
            if guide_info.get("moduleName") != "Child":
                if guide_info.get("moduleName") == "arm":
                    lbm.ArmModule(guide_name).make()
                if guide_info.get("moduleName") == "frontLeg":
                    lbm.FrontLegModule(guide_name).make()
                if guide_info.get("moduleName") == "leg":
                    lbm.LegModule(guide_name).make()
                if guide_info.get("moduleName") == "backLeg":
                    lbm.BackLegModule(guide_name).make()
                if guide_info.get("moduleName") == "hand":
                    han.HandModule().make(guide_name=guide_name)
                if guide_info.get("moduleName") == "spine":
                    if guide_info.get("type") == 0:
                        spm_bip.SpineModule().make(guide_name)
                    elif guide_info.get("type") == 1:
                        spm_quad.SpineModule().make(guide_name)
                if guide_info.get("moduleName") == "neck":
                    if guide_info.get("type") == 0:
                        nck_bip.NeckModule().make(guide_name)
                    elif guide_info.get("type") == 1:
                        nck_quad.NeckModule().make(guide_name)

    # skeleton_hierarchy = skh.build_complete_hierarchy() 
    # ss.make_spaces_quadruped()

    rename_ctl_shapes()
    joint_label()

    cmds.inViewMessage(
    amg=f'Completed <hl> {asset_name.capitalize()} RIG</hl> build.',
    pos='midCenter',
    fade=True,
    alpha=0.8)

    cmds.select(clear=True)


