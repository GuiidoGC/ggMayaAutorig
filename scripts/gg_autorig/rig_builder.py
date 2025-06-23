

# Tools / utils import
from gg_autorig.utils import basic_structure
from gg_autorig.utils import data_export
from gg_autorig.utils.guides import guides_manager
from gg_autorig.utils import curve_tool

# Python libraries import
import maya.cmds as cmds
import os
from importlib import reload

reload(basic_structure)
reload(data_export)
reload(guides_manager)

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



def make():
    """
    Build a complete dragon rig in Maya by creating basic structure, modules, and setting up space switching for controllers.
    This function initializes various modules, creates the basic structure, and sets up controllers and constraints for the rig.
    It also sets the radius for all joints and displays a completion message.
    """   

    complete_path = os.path.realpath(__file__)
    relative_path = complete_path.split("\scripts")[0]
    guides_path = os.path.join(relative_path, "guides", "aychedral_GUIDES_001.guides")
    curves_path = os.path.join(relative_path, "curves", "AYCHEDRAL_curves_001.json") 
    guides_manager.init_template_file(guides_path)
    curve_tool.init_template_file(curves_path)

    data_exporter = data_export.DataExport()
    data_exporter.new_build()

    basic_structure.create_basic_structure(asset_name = "AYCHEDRAL")
    
  
    rename_ctl_shapes()
    joint_label()

    cmds.inViewMessage(
    amg='Completed <hl>BIPED RIG</hl> build.',
    pos='midCenter',
    fade=True,
    alpha=0.8)

    cmds.select(clear=True)


