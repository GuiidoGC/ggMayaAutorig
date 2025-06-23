import maya.cmds as cmds


for item in cmds.ls(sl=True, type="transform"):
    pos = cmds.xform(item, q=True, ws=True, t=True)
    int_pos = [round(v, 2) for v in pos]
    print(f"{item}: {int_pos}")



# for item in cmds.ls(sl=True, type="transform"):
#     print(item)
#     shape = cmds.listRelatives(item, shapes=True)
#     print(shape)    
#     for s in shape:
#         print(s)
#         cmds.setAttr(f"{s}.alwaysDrawOnTop", 1)