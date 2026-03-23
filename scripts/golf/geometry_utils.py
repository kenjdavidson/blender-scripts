"""
Hole-In-One Geometry Utilities
================================
Handles the heavy lifting for the Hole-In-One Commemorative Generator:
scaling imported SVG objects, converting curves to meshes, and performing
Boolean carve operations to produce a layered 3D-printable plaque.
"""

import bpy

# --- CONSTANTS ---
BASE_OBJECT_NAME = "Hole_In_One_Base"
CUTTER_HEIGHT = 10.0
AUTO_SCALE_FACTOR = 0.9

# --- CONFIGURATION & COLOR MAP ---
# Each entry maps a layer name prefix to (z_depth_from_surface, RGBA_color).
# Layers with a higher depth value are carved deeper into the plaque.
COLOR_MAP = {
    "Water":   (3.0, (0.0, 0.3, 0.8, 1)),
    "Sand":    (2.4, (0.9, 0.8, 0.5, 1)),
    "Green":   (1.8, (0.1, 0.8, 0.1, 1)),
    "Tee":     (1.8, (0.9, 0.9, 0.9, 1)),
    "Fairway": (1.2, (0.05, 0.5, 0.05, 1)),
    "Rough":   (0.6, (0.02, 0.2, 0.02, 1)),
    "Text":    (0.0, (1.0, 1.0, 1.0, 1)),
}


def setup_material(name, color):
    """Return an existing ``Mat_<name>`` material or create a new one."""
    mat_name = f"Mat_{name}"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    mat.diffuse_color = color
    return mat


def sanitize_geometry(objects, props):
    """Convert curves to meshes, center origins, and scale all SVG objects.

    When *use_manual_scale* is ``False`` and a ``Rough`` object exists the
    plaque width drives the scale.  Otherwise the longest dimension of all
    objects is fitted inside 90 % of the smaller plaque dimension.
    """
    if not objects:
        return

    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        if obj.type == "CURVE":
            bpy.ops.object.convert(target="MESH")
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

    anchor = next(
        (obj for obj in objects if obj.name.startswith("Rough")), None
    )

    if not props.use_manual_scale and anchor:
        scale_ratio = props.plaque_width / anchor.dimensions.x
    else:
        max_svg_dim = max(
            max(obj.dimensions.x, obj.dimensions.y) for obj in objects
        )
        scale_ratio = (
            min(props.plaque_width, props.plaque_height) * AUTO_SCALE_FACTOR
        ) / max_svg_dim

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.ops.transform.resize(value=(scale_ratio, scale_ratio, scale_ratio))
    bpy.ops.object.transform_apply(scale=True)

    for obj in objects:
        obj.location = (0, 0, 0)


def carve_plaque(props):
    """Build the base plaque cube and Boolean-carve each SVG layer into it."""
    if BASE_OBJECT_NAME in bpy.data.objects:
        bpy.data.objects.remove(
            bpy.data.objects[BASE_OBJECT_NAME], do_unlink=True
        )

    bpy.ops.mesh.primitive_cube_add(size=1)
    base = bpy.context.active_object
    base.name = BASE_OBJECT_NAME
    base.scale = (props.plaque_width, props.plaque_height, props.plaque_thick)
    bpy.ops.object.transform_apply(scale=True)
    base.data.materials.append(setup_material("Rough", COLOR_MAP["Rough"][1]))

    all_svg_objs = [
        obj
        for obj in bpy.data.objects
        if any(obj.name.startswith(pre) for pre in COLOR_MAP)
        and obj != base
    ]

    sanitize_geometry(all_svg_objs, props)

    for prefix, (depth, color) in COLOR_MAP.items():
        cutters = [
            obj
            for obj in bpy.data.objects
            if obj.name.startswith(prefix) and obj != base
        ]
        mat = setup_material(prefix, color)

        for cutter in cutters:
            cutter.dimensions.z = CUTTER_HEIGHT
            cutter.location.z = (
                (props.plaque_thick / 2) - depth + (cutter.dimensions.z / 2)
            )
            if not cutter.data.materials:
                cutter.data.materials.append(mat)

            bool_mod = base.modifiers.new(
                type="BOOLEAN", name=f"Cut_{cutter.name}"
            )
            bool_mod.object = cutter
            bool_mod.operation = "DIFFERENCE"
            bool_mod.solver = "EXACT"

            cutter.display_type = "WIRE"
            cutter.hide_render = True
