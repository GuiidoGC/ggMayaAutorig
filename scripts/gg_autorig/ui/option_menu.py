import maya.cmds as cmds
from functools import partial
import os
from importlib import reload

from gg_autorig.ui import option_menu
from gg_autorig.utils.guides import guides_manager 
from gg_autorig.utils import curve_tool  
reload(curve_tool)




def reload_ui(*args):
    """
    Function to reload the Puiastre Productions UI.

    Args:
        *args: Variable length argument list, not used in this function.
    """
    reload(option_menu)
    option_menu.gg_autorig_ui()

def export_guides(*args): 
    """
    Function to export selected guides from the scene.

    Args:
        *args: Variable length argument list, not used in this function.
    """ 
    guides_manager.guides_export()



def export_curves(*args, curves_path): 
    """
    Function to export all controller curves data.

    Args:
        *args: Variable length argument list, not used in this function.
    """
    curve_tool.init_template_file(curves_path)
    curve_tool.get_all_ctl_curves_data(prefix="GUIDE")

def gg_autorig_ui():
    """
    Create the Puiastre Productions menu in Maya.
    """

    complete_path = os.path.realpath(__file__)
    relative_path = complete_path.split("\scripts")[0]
    curves_path = os.path.join(relative_path, "curves", "guides_curves_template.json") 

    if cmds.menu("AutorigMenu", exists=True):
        cmds.deleteUI("AutorigMenu")
    cmds.menu("AutorigMenu", label="GG AUTORIG", tearOff=True, parent="MayaWindow")

    cmds.menuItem(label="   Settings", subMenu=True, tearOff=True, boldFont=True)
    cmds.menuItem(label="   Reload UI", command=reload_ui)

    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)


    cmds.menuItem(label="   Guides", subMenu=True, tearOff=True, boldFont=True)
    cmds.menuItem(label="   Export selected Guides", command=export_guides)
    # cmds.menuItem(label="   Import Guides", command=partial(import_guides, value = True))
    # cmds.menuItem(label="   Import selected Guides", optionBox=True, command=partial(import_guides, value = None))
    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)

    cmds.menuItem(label="   Controls", subMenu=True, tearOff=True, boldFont=True)
    cmds.menuItem(label="   Export all controllers", command=partial(export_curves, curves_path=curves_path))
    # cmds.menuItem(label="   Mirror all L_ to R_", command=mirror_ctl)
    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)

    cmds.menuItem(label="   Rig", subMenu=True, tearOff=True, boldFont=True)
    # cmds.menuItem(label="   Complete Rig (dev only)", command=complete_rig)
    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)

    cmds.menuItem(label="   Animation", subMenu=True, tearOff=True, boldFont=True)
    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)

    cmds.menuItem(label="   Skin Cluster", subMenu=True, tearOff=True, boldFont=True)
    cmds.menuItem(label="   Export Skin Data")
    cmds.menuItem(label="   Import Skin Data")
    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)

    cmds.setParent("..", menu=True)
