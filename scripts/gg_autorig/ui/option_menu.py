import maya.cmds as cmds
from functools import partial
import os
from importlib import reload

from gg_autorig.ui import option_menu
from gg_autorig.ui import ui




def reload_ui(*args):
    """
    Function to reload the Puiastre Productions UI.

    Args:
        *args: Variable length argument list, not used in this function.
    """
    reload(option_menu)
    option_menu.gg_autorig_ui()

def rig_ui(*args):
    """
    Function to open the Autorig UI for creating a complete rig.
    Args:
        *args: Variable length argument list, not used in this function.
    """
    # In case the UI is already open, close it first
    try:
        toolboxInstance.close()
    except:
        pass

    # Create a new instance of the GG_Toolbox UI
    toolboxInstance = ui.GG_Toolbox()
    toolboxInstance.show()

def gg_autorig_ui():
    """
    Create the GG Toolbox menu in Maya.
    """

    if cmds.menu("GG rig", exists=True):
        cmds.deleteUI("GG rig")
    cmds.menu("GG rig", label="GG rig", tearOff=True, parent="MayaWindow")

    cmds.menuItem(label="   Settings", subMenu=True, tearOff=True, boldFont=True)
    cmds.menuItem(label="   Reload UI", command=reload_ui)

    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)

    cmds.menuItem(label="   Autorig", subMenu=True, tearOff=True, boldFont=True)
    cmds.menuItem(label="   Autorig - UI", command=rig_ui)
    cmds.setParent("..", menu=True)
    cmds.menuItem(dividerLabel="\n ", divider=True)


    cmds.setParent("..", menu=True)
