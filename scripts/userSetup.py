import maya.utils as mu
import maya.cmds as cmds

"""
This script sets up the Maya environment by creating command ports and loading the ToolBox UI.
It also executes a deferred command to load the UI after Maya has fully initialized.
"""

if not cmds.commandPort(":4434", query=True):
    cmds.commandPort(name=":4434")
if not cmds.commandPort("localhost:7001", query=True):
    cmds.commandPort(name="localhost:7001")

mu.executeDeferred("from gg_autorig.ui import option_menu; option_menu.gg_autorig_ui()")
