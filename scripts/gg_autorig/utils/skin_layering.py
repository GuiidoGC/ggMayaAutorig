import maya.cmds as cmds
from ngSkinTools2.api import init_layers
import maya.api.OpenMaya as om

# Tools / utils import
from gg_autorig.utils import data_export

def setup_ngskintools_layers(mesh_name,):

    data_exporter = data_export.DataExport()

    skelHierarchy_grp = data_exporter.get_data("basic_structure", "skeletonHierarchy_GRP")
    skinning_joints = cmds.listRelatives(skelHierarchy_grp, allDescendents=True, fullPath=True, type="joint")

    if not cmds.objExists(mesh_name):
        cmds.error("Specified mesh '{}' does not exist.".format(mesh_name))
    shapes = cmds.listRelatives(mesh_name, shapes=True, fullPath=True) or []
    mesh_shapes = [s for s in shapes if cmds.objectType(s) == "mesh"]
    if not mesh_shapes:
        cmds.error("'{}' is not a polygon mesh.".format(mesh_name))
    
    for j in skinning_joints:
        if not cmds.objExists(j):
            cmds.error("Joint '{}' does not exist.".format(j))
        if cmds.nodeType(j) != "joint":
            cmds.error("'{}' is not a joint.".format(j))
    
    skincluster = cmds.skinCluster(skinning_joints, mesh_name, toSelectedBones=True, normalizeWeights=1)[0]
    print("skinCluster '{}' created.".format(skincluster))
    
    layers = init_layers(skincluster)

    layer_blocking = layers.add("BLOCKING")
    layer_spline = layers.add("SPLINE")
    layer_twists = layers.add("TWISTS")
    layer_upperarm = layers.add("UPPERARM", parent=layer_twists)
    layer_lowerarm = layers.add("LOWERARM", parent=layer_twists)
    layer_upperleg = layers.add("UPPERLEG", parent=layer_twists)
    layer_lowerleg = layers.add("LOWERLEG", parent=layer_twists)
    layer_spine = layers.add("SPINE", parent=layer_twists)


setup_ngskintools_layers("C_body_MSH")