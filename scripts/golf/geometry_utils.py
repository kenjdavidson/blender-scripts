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

# Name prefixes that identify a dedicated plaque base imported from SVG.
# These objects are NOT used as cutters – they define the outer frame boundary.
PLAQUE_BASE_PREFIXES = ("Plaque_Base", "Plaque_Frame")

# Extra margin (mm) added to each side when auto-generating a protective frame
# from the Rough boundary.
PROTECTIVE_FRAME_MARGIN = 2.0

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


def find_plaque_base(objects=None):
    """Return the first object named ``Plaque_Base`` or ``Plaque_Frame``, or ``None``.

    *objects* may be any iterable of ``bpy.types.Object``; when omitted the
    full ``bpy.data.objects`` collection is searched.
    """
    search = objects if objects is not None else bpy.data.objects
    for obj in search:
        if any(obj.name.startswith(pre) for pre in PLAQUE_BASE_PREFIXES):
            return obj
    return None


def sanitize_geometry(objects, props):
    """Convert curves to meshes, center origins, and scale all SVG objects.

    When *use_manual_scale* is ``False`` and a ``Rough`` object exists the
    plaque width drives the scale.  Otherwise the longest dimension of all
    objects is fitted inside 90 % of the smaller plaque dimension.

    Objects whose names start with :data:`PLAQUE_BASE_PREFIXES` are included
    in the scaling pass so that their dimensions are correct before
    :func:`carve_plaque` reads them.
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
    """Build the base plaque cube and Boolean-carve each SVG layer into it.

    Target-selection logic
    ~~~~~~~~~~~~~~~~~~~~~~
    1. If the scene contains an object named ``Plaque_Base`` or
       ``Plaque_Frame`` (imported from SVG), its XY extents are used as the
       frame dimensions and the object is hidden from the render.
    2. Else, if *props.generate_protective_frame* is ``True`` and a ``Rough``
       object is present, the frame is sized to Rough's XY extents plus a
       :data:`PROTECTIVE_FRAME_MARGIN` border on every side.
    3. Else, the plaque width/height from *props* is used (original behaviour).

    A solid cube is always created as the Boolean target so that Boolean
    modifiers have a valid manifold mesh to operate on.

    Z-order
    ~~~~~~~
    Cutters are applied shallowest-first (ascending depth) so that the Rough
    pocket is carved before the deeper Fairway / Green / Sand features.  This
    avoids artefacts where a deeper Boolean would otherwise remove geometry
    that a shallower cutter still needs.
    """
    if BASE_OBJECT_NAME in bpy.data.objects:
        bpy.data.objects.remove(
            bpy.data.objects[BASE_OBJECT_NAME], do_unlink=True
        )

    # Collect all recognised SVG objects (cutters + optional Plaque_Base).
    all_known_prefixes = tuple(COLOR_MAP.keys()) + PLAQUE_BASE_PREFIXES
    all_svg_objs = [
        obj
        for obj in bpy.data.objects
        if any(obj.name.startswith(pre) for pre in all_known_prefixes)
    ]

    sanitize_geometry(all_svg_objs, props)

    # --- Determine base (frame) dimensions ---
    plaque_base_svg = find_plaque_base()
    rough_obj = next(
        (o for o in bpy.data.objects if o.name.startswith("Rough")), None
    )

    if plaque_base_svg is not None:
        # Use the imported Plaque_Base / Plaque_Frame boundary.
        base_x = plaque_base_svg.dimensions.x
        base_y = plaque_base_svg.dimensions.y
        # Hide the reference object; it is not a Boolean cutter.
        plaque_base_svg.display_type = "WIRE"
        plaque_base_svg.hide_render = True
    elif props.generate_protective_frame and rough_obj is not None:
        # Auto-generate a frame slightly larger than the Rough area.
        base_x = rough_obj.dimensions.x + PROTECTIVE_FRAME_MARGIN * 2
        base_y = rough_obj.dimensions.y + PROTECTIVE_FRAME_MARGIN * 2
    else:
        # Fall back to the user-supplied plaque dimensions.
        base_x = props.plaque_width
        base_y = props.plaque_height

    # --- Build the solid base cube ---
    bpy.ops.mesh.primitive_cube_add(size=1)
    base = bpy.context.active_object
    base.name = BASE_OBJECT_NAME
    base.scale = (base_x, base_y, props.plaque_thick)
    bpy.ops.object.transform_apply(scale=True)
    base.data.materials.append(setup_material("Rough", COLOR_MAP["Rough"][1]))

    # --- Apply Boolean cutters, shallowest depth first ---
    # Sorting ascending by depth ensures Rough (0.6 mm) is carved before the
    # deeper Fairway / Green / Sand layers, producing clean intersections.
    sorted_items = sorted(COLOR_MAP.items(), key=lambda item: item[1][0])

    for prefix, (depth, color) in sorted_items:
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
            # TODO: add additional cutter modifications here (e.g. draft angles,
            # displacement modifiers, or other per-cutter transformations) before
            # the Boolean modifier is applied below.
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
