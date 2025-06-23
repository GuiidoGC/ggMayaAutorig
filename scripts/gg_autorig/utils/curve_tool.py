import maya.api.OpenMaya as om
import maya.cmds as cmds
import json
import os


TEMPLATE_FILE = None

def init_template_file(path=None):
    """
    Initializes the TEMPLATE_FILE variable.
    If a path is provided, it sets TEMPLATE_FILE to that path.
    Otherwise, it uses the default template file path.
    """
    global TEMPLATE_FILE
    if path:
        TEMPLATE_FILE = path
    else:
        complete_path = os.path.realpath(__file__)
        relative_path = complete_path.split("\scripts")[0]
        TEMPLATE_FILE = os.path.join(relative_path, "curves", "template_curves_001.json")

def lock_attr(ctl, attrs = ["scaleX", "scaleY", "scaleZ", "visibility"], ro=True):
    """
    Lock specified attributes of a controller, added rotate order attribute if ro is True.
    
    Args:
        ctl (str): The name of the controller to lock attributes on.
        attrs (list): List of attributes to lock. Default is ["scaleX", "scaleY", "scaleZ", "visibility"].
        ro (bool): If True, adds a rotate order attribute. Default is True.
    """

    for attr in attrs:
        cmds.setAttr(f"{ctl}.{attr}", keyable=False, channelBox=False, lock=True)
    
    if ro:
        cmds.addAttr(ctl, longName="rotate_order", nn="Rotate Order", attributeType="enum", enumName="xyz:yzx:zxy:xzy:yxz:zyx", keyable=True)
        cmds.connectAttr(f"{ctl}.rotate_order", f"{ctl}.rotateOrder")

def get_all_ctl_curves_data(prefix="CTL"):
    """
    Collects data from all controller curves in the scene and saves it to a JSON file.
    This function retrieves information about each controller's transform and its associated nurbsCurve shapes,
    including their CV positions, form, knots, degree, and override attributes.
    """

    ctl_data = {}

    transforms = cmds.ls(f"*_{prefix}*", type="transform", long=True)

    for transform_name in transforms:
        shapes = cmds.listRelatives(transform_name, shapes=True, fullPath=True) or []
        nurbs_shapes = []

        for shape in shapes:
            if cmds.nodeType(shape) == "nurbsCurve":
                nurbs_shapes.append(shape)

        if not nurbs_shapes:
            continue  

        sel_list = om.MSelectionList()
        sel_list.add(transform_name)
        transform_obj = sel_list.getDependNode(0)

        def get_override_info(node_obj):
            fn_dep = om.MFnDependencyNode(node_obj)
            try:
                override_enabled = fn_dep.findPlug('overrideEnabled', False).asBool()
                override_color = fn_dep.findPlug('overrideColor', False) if override_enabled else None
                override_color_value = override_color.asInt() if override_color else None
            except:
                override_enabled = False
                override_color_value = None
            return override_enabled, override_color_value

        transform_override_enabled, transform_override_color = get_override_info(transform_obj)

        shape_data_list = []

        for shape in nurbs_shapes:
            sel_list.clear()
            sel_list.add(shape)
            shape_obj = sel_list.getDependNode(0)

            shape_override_enabled, shape_override_color = get_override_info(shape_obj)

            fn_shape_dep = om.MFnDependencyNode(shape_obj)
            try:
                always_on_top = fn_shape_dep.findPlug('alwaysDrawOnTop', False).asBool()
            except:
                always_on_top = False

            curve_fn = om.MFnNurbsCurve(shape_obj)

            cvs = []
            for i in range(curve_fn.numCVs):
                pt = curve_fn.cvPosition(i)
                cvs.append((pt.x, pt.y, pt.z))

            form_types = {
                om.MFnNurbsCurve.kOpen: "open",
                om.MFnNurbsCurve.kClosed: "closed",
                om.MFnNurbsCurve.kPeriodic: "periodic"
            }

            line_width = None
            if cmds.attributeQuery("lineWidth", node=shape, exists=True):
                try:
                    line_width = cmds.getAttr(shape + ".lineWidth")
                except:
                    pass 

            form = form_types.get(curve_fn.form, "unknown")
            if form == "unknown":
                om.MGlobal.displayWarning(f"Curve form unknown for {shape}")

            knots = curve_fn.knots()
            degree = curve_fn.degree

            shape_data_list.append({
                "name": shape.split("|")[-1],
                "overrideEnabled": shape_override_enabled,
                "overrideColor": shape_override_color,
                "alwaysDrawOnTop": always_on_top,
                "lineWidth": line_width,
                "curve": {
                    "cvs": cvs,
                    "form": form,
                    "knots": list(knots),
                    "degree": degree
                }
            })

        ctl_data[transform_name] = {
            "transform": {
                "name": transform_name.split("|")[-1],
                "overrideEnabled": transform_override_enabled,
                "overrideColor": transform_override_color
            },
            "shapes": shape_data_list
        }

    with open(TEMPLATE_FILE, "w") as f:
        json.dump(ctl_data, f, indent=4)

    print(f"Controllers template saved to: {TEMPLATE_FILE}")

def build_curves_from_template(target_transform_name=None):
    """
    Builds controller curves from a predefined template JSON file.
    If a specific target transform name is provided, it filters the curves to only create those associated with that transform.
    If no target transform name is provided, it creates all curves defined in the template.
    Args:
        target_transform_name (str, optional): The name of the target transform to filter curves by. Defaults to None.
    Returns:
        list: A list of created transform names.
    """

    if not os.path.exists(TEMPLATE_FILE):
        om.MGlobal.displayError("Template file does not exist.")
        return

    with open(TEMPLATE_FILE, "r") as f:
        ctl_data = json.load(f)

    if target_transform_name:
        ctl_data = {k: v for k, v in ctl_data.items() if v["transform"]["name"] == target_transform_name}
        if not ctl_data:
            return

    created_transforms = []

    for transform_path, data in ctl_data.items():
        transform_info = data["transform"]
        shape_data_list = data["shapes"]

        dag_modifier = om.MDagModifier()
        transform_obj = dag_modifier.createNode("transform")
        dag_modifier.doIt()

        transform_fn = om.MFnDagNode(transform_obj)
        final_name = transform_fn.setName(transform_info["name"])
        created_transforms.append(final_name)

        if transform_info["overrideEnabled"]:
            fn_dep = om.MFnDependencyNode(transform_obj)
            fn_dep.findPlug('overrideEnabled', False).setBool(True)
            fn_dep.findPlug('overrideColor', False).setInt(transform_info["overrideColor"])

        created_shapes = []

        for shape_data in shape_data_list:
            curve_info = shape_data["curve"]
            cvs = curve_info["cvs"]
            degree = curve_info["degree"]
            knots = curve_info["knots"]
            form = curve_info["form"]

            form_flags = {
                "open": om.MFnNurbsCurve.kOpen,
                "closed": om.MFnNurbsCurve.kClosed,
                "periodic": om.MFnNurbsCurve.kPeriodic
            }
            form_flag = form_flags.get(form, om.MFnNurbsCurve.kOpen)

            points = om.MPointArray()
            for pt in cvs:
                points.append(om.MPoint(pt[0], pt[1], pt[2]))

            curve_fn = om.MFnNurbsCurve()
            shape_obj = curve_fn.create(
                points,
                knots,
                degree,
                form_flag,
                False,    
                True,     
                transform_obj
            )

            shape_fn = om.MFnDagNode(shape_obj)
            shape_fn.setName(shape_data["name"])

            if shape_data["overrideEnabled"]:
                fn_dep = om.MFnDependencyNode(shape_obj)
                fn_dep.findPlug('overrideEnabled', False).setBool(True)
                fn_dep.findPlug('overrideColor', False).setInt(shape_data["overrideColor"])

            if shape_data.get("alwaysDrawOnTop", False):
                fn_dep = om.MFnDependencyNode(shape_obj)
                fn_dep.findPlug('alwaysDrawOnTop', False).setBool(True)

            line_width = shape_data.get("lineWidth", None)
            if line_width is not None:
                if cmds.attributeQuery("lineWidth", node=shape_fn.name(), exists=True):
                    try:
                        cmds.setAttr(shape_fn.name() + ".lineWidth", line_width)
                    except:
                        om.MGlobal.displayWarning(f"Could not set lineWidth for {shape_fn.name()}")

            created_shapes.append(shape_obj)


    return created_transforms


def controller_creator(name, suffixes=["GRP", "ANM"], mirror=False, parent=None, match=None, lock=["scaleX", "scaleY", "scaleZ", "visibility"], ro=True, prefix="CTL"):
    """
    Creates a controller with a specific name and offset transforms and returns the controller and the groups.

    Args:
        name (str): Name of the controller.
        suffixes (list): List of suffixes for the groups to be created. Default is ["GRP"].
    """
    created_grps = []
    if suffixes:
        for suffix in suffixes:
            if cmds.ls(f"{name}_{suffix}"):
                om.MGlobal.displayWarning(f"{name}_{suffix} already exists.")
                if created_grps:
                    cmds.delete(created_grps[0])
                return
            tra = cmds.createNode("transform", name=f"{name}_{suffix}", ss=True)
            if created_grps:
                cmds.parent(tra, created_grps[-1])
            created_grps.append(tra)

    if cmds.ls(f"{name}_{prefix}"):
        om.MGlobal.displayWarning(f"{name}_{prefix} already exists.")
        if created_grps:
            cmds.delete(created_grps[0])
        return
    else:
        ctl = build_curves_from_template(f"{name}_{prefix}")

        if not ctl:
            ctl = cmds.circle(name=f"{name}_{prefix}", ch=False)
        else:
            ctl = [ctl[0]]

        if created_grps:
            cmds.parent(ctl[0], created_grps[-1])
    
        if match:
            if cmds.objExists(match):
                cmds.xform(ctl[0], ws=True, t=cmds.xform(match, q=True, ws=True, t=True))
                cmds.xform(ctl[0], ws=True, ro=cmds.xform(match, q=True, ws=True, ro=True))

        if parent:
            if cmds.objExists(parent):
                if created_grps:
                    cmds.parent(created_grps[0], parent)
                else:
                    cmds.parent(ctl[0], parent)


        if mirror:
            force_behavior_mirror(created_grps[0])

        lock_attr(ctl[0], lock, ro)

    if created_grps:
        return ctl[0], created_grps
    else:
        return ctl[0]



def force_behavior_mirror(node):

    """Mirrors the transform of a given node along the X-axis.
    It adjusts the translation and rotation values to achieve the mirroring effect.

    Args:
        node (str): The name of the node to mirror.
    """

    t = cmds.xform(node, q=True, ws=True, t=True)
    r = cmds.xform(node, q=True, ws=True, ro=True)

    mirrored_t = [-t[0], t[1], t[2]]
    mirrored_r = [(r[0] + 180) % 360, -r[1], -r[2]]

    for i in range(3):
        if mirrored_r[i] > 180:
            mirrored_r[i] -= 360

    cmds.xform(node, ws=True, t=mirrored_t, ro=mirrored_r)  

    name = node.replace("_GRP", "mirrored_GRP")
    mirror_transform = cmds.createNode("transform", name=name, ss=True)

    parent = cmds.listRelatives(node, parent=True, fullPath=True)
    if parent:
        cmds.parent(mirror_transform, parent[0])

    cmds.parent(node, mirror_transform)


def mirror_shapes():
    left_side = 'L_'
    right_side = 'R_'
    suffix = '_CTL'

    color_map = {
        6: 13,
        18: 4
    }

    all_ctls = cmds.ls(type='transform')
    source_ctls = []
    for tr in all_ctls:
        if suffix in tr:
            shapes = cmds.listRelatives(tr, shapes=True) or []
            if any(cmds.nodeType(s) == 'nurbsCurve' for s in shapes):
                source_ctls.append(tr)

    for src in source_ctls:
        if not src.startswith(left_side):
            continue

        tgt = src.replace(left_side, right_side, 1)
        src_shapes = cmds.listRelatives(src, shapes=True, fullPath=True) or []

        if not cmds.objExists(tgt):
            cmds.warning(f"No matching right-side transform for {src}, expected {tgt}")
            continue

        trans_override = cmds.getAttr(f'{src}.overrideEnabled')
        cmds.setAttr(f'{tgt}.overrideEnabled', trans_override)

        if trans_override:
            src_col = cmds.getAttr(f'{src}.overrideColor')
            tgt_col = color_map.get(src_col, src_col)
            cmds.setAttr(f'{tgt}.overrideColor', tgt_col)

        tgt_shapes = cmds.listRelatives(tgt, shapes=True, fullPath=True) or []
        for s in tgt_shapes:
            cmds.delete(s)

        for i, src_shape in enumerate(src_shapes):
            dup_tr = cmds.duplicate(src, name=src + '_dup')[0]
            dup_shapes = cmds.listRelatives(dup_tr, shapes=True, fullPath=True)
            dup_shape = dup_shapes[i] if i < len(dup_shapes) else dup_shapes[0]

            new_shape = cmds.parent(dup_shape, tgt, shape=True, relative=True)[0]
            shape_name = f'{tgt}Shape{i+1:02d}'
            new_shape = cmds.rename(new_shape, shape_name)

            cmds.delete(dup_tr)

            num_cvs = cmds.getAttr(f'{src_shape}.spans') + cmds.getAttr(f'{src_shape}.degree')
            for pt_idx in range(num_cvs + 1):
                pt = cmds.xform(f'{src_shape}.controlPoints[{pt_idx}]', q=True, t=True, ws=True)
                cmds.xform(f'{new_shape}.controlPoints[{pt_idx}]', t=(-pt[0], pt[1], pt[2]), ws=True)

            if cmds.attributeQuery('lineWidth', node=src_shape, exists=True):
                line_width = cmds.getAttr(f'{src_shape}.lineWidth')
                cmds.setAttr(f'{new_shape}.lineWidth', line_width)

            shape_override = cmds.getAttr(f'{src_shape}.overrideEnabled')
            cmds.setAttr(f'{new_shape}.overrideEnabled', shape_override)

            if shape_override:
                draw_type = cmds.getAttr(f'{src_shape}.overrideDisplayType')
                cmds.setAttr(f'{new_shape}.overrideDisplayType', draw_type)

                src_col = cmds.getAttr(f'{src_shape}.overrideColor')
                tgt_col = color_map.get(src_col, src_col)
                cmds.setAttr(f'{new_shape}.overrideColor', tgt_col)

        print(f"Mirrored {len(src_shapes)} shapes from {src} → {tgt}")