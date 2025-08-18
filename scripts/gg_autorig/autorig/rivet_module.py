#Python libraries import
from maya import cmds
from importlib import reload
import maya.api.OpenMaya as om
import math

# Local imports
from gg_autorig.utils.curve_tool import controller_creator
from gg_autorig.utils.guides.guides_manager import guide_import
from gg_autorig.utils import data_export

# Dev only imports
from gg_autorig.utils.guides import guides_manager
reload(guides_manager)



def river_joint(mesh = "C_body_MSH", guide_name = ""):

    """
    Create a limb rig with controllers and constraints.
    This function sets up the basic structure for a limb, including controllers and constraints.
    """     

    data_exporter = data_export.DataExport()

    modules_grp = data_exporter.get_data("basic_structure", "modules_GRP")
    skel_grp = data_exporter.get_data("basic_structure", "skel_GRP")
    masterWalk_ctl = data_exporter.get_data("basic_structure", "masterWalk_CTL")

    guides = guide_import(guide_name, all_descendents=True, path=None)

    name = guide_name.replace("_GUIDE", "")

    individual_module_grp = cmds.createNode("transform", name=f"{name}Module_GRP", parent=modules_grp, ss=True)
    skinnging_grp = data_exporter.get_data("rivet_module", "skinningJoints_GRP")
    if not skinnging_grp:
        skinnging_grp = cmds.createNode("transform", name=f"{name}ModuleJoints_GRP", parent=skel_grp, ss=True)

    target_pos = cmds.xform(guides, query=True, worldSpace=True, translation=True)
    target_point = om.MVector(target_pos)

    sel_list = om.MSelectionList()
    sel_list.add(mesh)
    dag_path = sel_list.getDagPath(0)
    mesh_fn = om.MFnMesh(dag_path)

    vertex_positions = mesh_fn.getPoints(om.MSpace.kWorld)

    min_dist = float('inf')
    closest_index = -1

    for i, pos in enumerate(vertex_positions):
        dist = (target_point - om.MVector(pos)).length()
        if dist < min_dist:
            min_dist = dist
            closest_index = i

    vertex_iter = om.MItMeshVertex(dag_path)
    vertex_iter.setIndex(closest_index)

    connected_faces = vertex_iter.getConnectedFaces()[0]

    all_edges = cmds.polyListComponentConversion(f'{mesh}.f[{connected_faces}]', fromFace=True, toEdge=True, border=True)
    cmds.select(all_edges, replace=True)
    all_edges = cmds.ls(all_edges, flatten=True)

    pair_one = []
    opposite_edges = []

    reference_edge = all_edges[0]
    pair_one.append(reference_edge)
    
    ref_edge_verts = set(cmds.ls(cmds.polyListComponentConversion(reference_edge, fromEdge=True, toVertex=True), flatten=True))

    remaining_edges = all_edges[1:]
    
    for i, edge_to_check in enumerate(remaining_edges):
        verts_to_check = set(cmds.ls(cmds.polyListComponentConversion(edge_to_check, fromEdge=True, toVertex=True), flatten=True))
        
        if ref_edge_verts.isdisjoint(verts_to_check):
            pair_one.append(edge_to_check)
            
            remaining_edges.pop(i)
            opposite_edges = remaining_edges
            break

    cmds.delete(guides)
    
    loft = cmds.loft(opposite_edges, name=f"{name}_LOFT", uniform=True)

    point_on_surface = cmds.createNode("pointOnSurfaceInfo", name=f"{name}_POSI", ss=True)
    cmds.connectAttr(f"{loft[1]}.outputSurface", f"{point_on_surface}.inputSurface", force=True)

    cmds.delete(loft[0])
    loft_node = cmds.rename(loft[1], f"{name}_LOFT")

    matrix_node = cmds.createNode('fourByFourMatrix', name=f"{name}4B4M", ss=True)

    cmds.connectAttr(f"{point_on_surface}.normalizedNormalX", f"{matrix_node}.in10", force=True)
    cmds.connectAttr(f"{point_on_surface}.normalizedNormalY", f"{matrix_node}.in11", force=True)
    cmds.connectAttr(f"{point_on_surface}.normalizedNormalZ", f"{matrix_node}.in12", force=True)

    cmds.connectAttr(f"{point_on_surface}.normalizedTangentVX", f"{matrix_node}.in00", force=True)
    cmds.connectAttr(f"{point_on_surface}.normalizedTangentVY", f"{matrix_node}.in01", force=True)
    cmds.connectAttr(f"{point_on_surface}.normalizedTangentVZ", f"{matrix_node}.in02", force=True)

    cmds.connectAttr(f"{point_on_surface}.normalizedTangentUX", f"{matrix_node}.in20", force=True)
    cmds.connectAttr(f"{point_on_surface}.normalizedTangentUY", f"{matrix_node}.in21", force=True)
    cmds.connectAttr(f"{point_on_surface}.normalizedTangentUZ", f"{matrix_node}.in22", force=True)

    cmds.connectAttr(f"{point_on_surface}.positionX", f"{matrix_node}.in30", force=True)
    cmds.connectAttr(f"{point_on_surface}.positionY", f"{matrix_node}.in31", force=True)
    cmds.connectAttr(f"{point_on_surface}.positionZ", f"{matrix_node}.in32", force=True)

    cmds.setAttr(f"{point_on_surface}.turnOnPercentage", 1)

    ctl, ctl_grp = controller_creator(
                name=name,
                suffixes=["GRP", "NEG"],
                lock=["scaleX", "scaleY", "scaleZ", "visibility"],
                ro=True,
            )
    
    cmds.setAttr(f"{ctl_grp[0]}.inheritsTransform", 0)
    cmds.parent(ctl_grp[0], masterWalk_ctl)

    pick_matrix = cmds.createNode("pickMatrix", name=f"{name}_PMX", ss=True)
    cmds.connectAttr(f"{masterWalk_ctl}.worldMatrix[0]", f"{pick_matrix}.inputMatrix", force=True)
    cmds.connectAttr(f"{pick_matrix}.outputMatrix", f"{ctl}.offsetParentMatrix", force=True)
    cmds.setAttr(f"{pick_matrix}.useShear", 0)
    cmds.setAttr(f"{pick_matrix}.useRotate", 0)
    cmds.setAttr(f"{pick_matrix}.useTranslate", 0)


    cmds.connectAttr(f"{matrix_node}.output", f"{ctl_grp[0]}.offsetParentMatrix", force=True)

    decompose_matrix = cmds.createNode("decomposeMatrix", name=f"{name}_DM", ss=True)
    cmds.connectAttr(f"{ctl}.inverseMatrix", f"{decompose_matrix}.inputMatrix", force=True)
    cmds.connectAttr(f"{decompose_matrix}.outputTranslate", f"{ctl_grp[1]}.translate", force=True)
    cmds.connectAttr(f"{decompose_matrix}.outputRotate", f"{ctl_grp[1]}.rotate", force=True)
    cmds.connectAttr(f"{decompose_matrix}.outputScale", f"{ctl_grp[1]}.scale", force=True)
    
    joint_offset = cmds.createNode("transform", name=f"{name}Offset_TRN", ss=True, parent=individual_module_grp)
    cmds.matchTransform(joint_offset, ctl_grp[0])
    joint = cmds.createNode("joint", name=f"{name}_JNT", parent=joint_offset, ss=True)
    cmds.connectAttr(f"{ctl}.matrix", f"{joint}.offsetParentMatrix", force=True)

    joint_env = cmds.createNode("joint", name=f"{name}_ENV", parent=skinnging_grp, ss=True)
    cmds.connectAttr(f"{joint}.worldMatrix[0]", f"{joint_env}.offsetParentMatrix", force=True)

    cmds.setAttr(f"{joint}.translateX", 0)
    cmds.setAttr(f"{joint}.translateY", 0)
    cmds.setAttr(f"{joint}.translateZ", 0)



river_joint(guide_name="L_BellyJiggle_GUIDE")