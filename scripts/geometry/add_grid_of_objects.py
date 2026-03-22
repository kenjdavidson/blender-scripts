"""
Add Grid of Objects
====================
Instantiates the active object (or a chosen mesh type) in a regular
grid pattern with configurable spacing, row count, and column count.

Usage:
    Select (or create) an object, then run from Blender's Scripting
    workspace or Text Editor.
"""

import bpy
import math


def add_grid_of_objects(
    rows=5,
    cols=5,
    spacing_x=2.0,
    spacing_y=2.0,
    use_active_object=True,
    mesh_type="CUBE",
):
    """Create a grid of objects in the current scene.

    Args:
        rows: Number of rows.
        cols: Number of columns.
        spacing_x: Distance between columns along the X axis.
        spacing_y: Distance between rows along the Y axis.
        use_active_object: If True, duplicate the active object;
                           otherwise add a new primitive of *mesh_type*.
        mesh_type: Primitive type to add when *use_active_object* is False.
                   One of: "CUBE", "SPHERE", "CYLINDER", "CONE", "TORUS".

    Returns:
        List of newly created objects.
    """
    created = []

    source_obj = bpy.context.active_object if use_active_object else None

    # Center the grid around the origin
    offset_x = -(cols - 1) * spacing_x / 2.0
    offset_y = -(rows - 1) * spacing_y / 2.0

    for row in range(rows):
        for col in range(cols):
            loc_x = offset_x + col * spacing_x
            loc_y = offset_y + row * spacing_y

            if source_obj is not None:
                # Duplicate the source object (linked copy)
                new_obj = source_obj.copy()
                new_obj.data = source_obj.data.copy()
                new_obj.location = (loc_x, loc_y, 0.0)
                bpy.context.collection.objects.link(new_obj)
                created.append(new_obj)
            else:
                # Add a new primitive at the target location
                _add_primitive(mesh_type, location=(loc_x, loc_y, 0.0))
                created.append(bpy.context.active_object)

    print(f"Created {len(created)} objects in a {rows}×{cols} grid.")
    return created


_PRIMITIVE_OPS = {
    "CUBE": bpy.ops.mesh.primitive_cube_add,
    "SPHERE": bpy.ops.mesh.primitive_uv_sphere_add,
    "CYLINDER": bpy.ops.mesh.primitive_cylinder_add,
    "CONE": bpy.ops.mesh.primitive_cone_add,
    "TORUS": bpy.ops.mesh.primitive_torus_add,
}


def _add_primitive(mesh_type, location):
    op = _PRIMITIVE_OPS.get(mesh_type.upper(), bpy.ops.mesh.primitive_cube_add)
    op(location=location)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    add_grid_of_objects(
        rows=4,
        cols=4,
        spacing_x=2.5,
        spacing_y=2.5,
        use_active_object=False,
        mesh_type="CUBE",
    )
