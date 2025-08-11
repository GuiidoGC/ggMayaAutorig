

# Tools / utils import
from gg_autorig.utils import basic_structure
from gg_autorig.utils import data_export
# from gg_autorig.utils.guides import guides_manager

# Rig modules import
from gg_autorig.autorig.quadruped import limb_module_quadruped as lbm
from gg_autorig.autorig.quadruped import spine_module_quadruped as spm
from gg_autorig.autorig.quadruped import neck_module_quadruped as nck
from gg_autorig.autorig.quadruped import skeleton_hierarchy as skh
from gg_autorig.autorig.quadruped import variable_fk as vfk
from gg_autorig.utils import space_switch as ss



# Python libraries import
import maya.cmds as cmds
from importlib import reload

reload(basic_structure)
reload(data_export)
reload(lbm)
reload(spm)
reload(nck)
reload(skh)
reload(ss)
reload(vfk)

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

    # modules_map = {
    #     "Arm Module": lbm.make,
    #     "Front Leg Module": spm.make,
    #     "Leg Module": lbm.FrontLegModule(side="L").make(),
    #     "Back Leg Module": lbm.BackLegModule(side="L").make(),
    #     "Spine Module": spm.SpineModule().make(),
    #     "Neck Module": nck.NeckModule().make(),
    # }
    # extra_modules_map = {
    #     "Variable FK": vfk.VariableFkModule(side="C", prefix="trunk").make(),
    #     "Rivet Module": vfk.RivetModule().make(),
    # }    

    # for side in ["L", "R"]:
    #     lbm.ArmModule(side=side).make()
    #     lbm.LegModule(side=side).make()



    # skeleton_hierarchy = skh.get_data()
    # ss.make_spaces_quadruped()

    # rename_ctl_shapes()
    # joint_label()

    # cmds.inViewMessage(
    # amg='Completed <hl>BIPED RIG</hl> build.',
    # pos='midCenter',
    # fade=True,
    # alpha=0.8)

    # cmds.select(clear=True)


