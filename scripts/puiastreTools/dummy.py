import maya.cmds as cmds

# name  = "BlendshapeRef_GEO"
# shape_ref = []
# for i, item in enumerate(cmds.ls(type="transform")):
#     if name in item:
#         child = item.replace(name, "_GEO")
#         blendshape = cmds.blendShape(child, item, name=f"blendshapeRef0{i}")[0]

#         cmds.setAttr(f"{blendshape}.{child}", 0)
#         cmds.setKeyframe(f"{blendshape}.{child}", time=-50)
#         cmds.setAttr(f"{blendshape}.{child}", 1)
#         cmds.setKeyframe(f"{blendshape}.{child}", time=0, value=1)

#     shape_ref.append(item)


for item in cmds.ls(sl=True):
    shape = cmds.listRelatives(item, shapes=True)
    for s in shape:
        cmds.setAttr(f"{s}.lineWidth", 2)