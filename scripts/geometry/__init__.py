"""
Geometry Utilities – Blender Addon
====================================
Entry point for the Geometry Utilities addon.  Registers Blender Operators
and an N-panel UI that wrap the helper functions in this package.

Install this addon by zipping the ``geometry/`` folder and installing it via
``Edit > Preferences > Add-ons > Install``, or by copying the folder into
Blender's user addons directory.
"""

bl_info = {
    "name": "Geometry Utilities",
    "author": "kenjdavidson",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Blender Scripts",
    "description": "Mesh creation and manipulation utilities",
    "category": "Mesh",
}

import bpy
from . import add_grid_of_objects

# ── Operator ─────────────────────────────────────────────────────────────────


class GEOMETRY_OT_AddGridOfObjects(bpy.types.Operator):
    """Instantiate an object or primitive in a regular N×M grid"""

    bl_idname = "geometry.add_grid_of_objects"
    bl_label = "Add Grid of Objects"
    bl_options = {"REGISTER", "UNDO"}

    rows: bpy.props.IntProperty(
        name="Rows",
        description="Number of rows in the grid",
        default=5,
        min=1,
        max=100,
    )
    cols: bpy.props.IntProperty(
        name="Columns",
        description="Number of columns in the grid",
        default=5,
        min=1,
        max=100,
    )
    spacing_x: bpy.props.FloatProperty(
        name="Spacing X",
        description="Distance between objects along the X axis",
        default=2.0,
        min=0.01,
        unit="LENGTH",
    )
    spacing_y: bpy.props.FloatProperty(
        name="Spacing Y",
        description="Distance between objects along the Y axis",
        default=2.0,
        min=0.01,
        unit="LENGTH",
    )
    use_active_object: bpy.props.BoolProperty(
        name="Use Active Object",
        description="Duplicate the active object; if disabled, add a new primitive",
        default=True,
    )
    mesh_type: bpy.props.EnumProperty(
        name="Mesh Type",
        description="Primitive to add when Use Active Object is disabled",
        items=[
            ("CUBE", "Cube", ""),
            ("SPHERE", "UV Sphere", ""),
            ("CYLINDER", "Cylinder", ""),
            ("CONE", "Cone", ""),
            ("TORUS", "Torus", ""),
        ],
        default="CUBE",
    )

    def execute(self, context):
        objects = add_grid_of_objects.add_grid_of_objects(
            rows=self.rows,
            cols=self.cols,
            spacing_x=self.spacing_x,
            spacing_y=self.spacing_y,
            use_active_object=self.use_active_object,
            mesh_type=self.mesh_type,
        )
        self.report(
            {"INFO"},
            f"Created {len(objects)} objects in a {self.rows}\u00d7{self.cols} grid",
        )
        return {"FINISHED"}


# ── Panel ─────────────────────────────────────────────────────────────────────


class GEOMETRY_PT_Panel(bpy.types.Panel):
    """Geometry utilities panel in the 3D Viewport sidebar"""

    bl_label = "Geometry Utilities"
    bl_idname = "GEOMETRY_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blender Scripts"

    def draw(self, context):
        layout = self.layout
        layout.operator("geometry.add_grid_of_objects", icon="MESH_GRID")


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    GEOMETRY_OT_AddGridOfObjects,
    GEOMETRY_PT_Panel,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
