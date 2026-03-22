"""
Material Utilities – Blender Addon
====================================
Entry point for the Material Utilities addon.  Registers Blender Operators
and an N-panel UI that wrap the helper functions in this package.

Install this addon by zipping the ``materials/`` folder and installing it via
``Edit > Preferences > Add-ons > Install``, or by copying the folder into
Blender's user addons directory.
"""

bl_info = {
    "name": "Material Utilities",
    "author": "kenjdavidson",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Blender Scripts",
    "description": "Material and shader node setup helpers",
    "category": "Material",
}

import bpy
from . import create_principled_material

# ── Operator ─────────────────────────────────────────────────────────────────


class MATERIAL_OT_CreatePrincipled(bpy.types.Operator):
    """Create a Principled BSDF material and assign it to the active object"""

    bl_idname = "material.create_principled"
    bl_label = "Create Principled Material"
    bl_options = {"REGISTER", "UNDO"}

    material_name: bpy.props.StringProperty(
        name="Name",
        description="Name for the new material",
        default="New Material",
    )
    base_color: bpy.props.FloatVectorProperty(
        name="Base Color",
        description="Diffuse base color (RGBA)",
        subtype="COLOR",
        size=4,
        default=(0.8, 0.2, 0.2, 1.0),
        min=0.0,
        max=1.0,
    )
    metallic: bpy.props.FloatProperty(
        name="Metallic",
        description="0 = non-metal, 1 = fully metallic",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    roughness: bpy.props.FloatProperty(
        name="Roughness",
        description="0 = mirror-like, 1 = fully diffuse",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    specular: bpy.props.FloatProperty(
        name="Specular",
        description="Specular intensity",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    def execute(self, context):
        mat = create_principled_material.create_principled_material(
            name=self.material_name,
            base_color=tuple(self.base_color),
            metallic=self.metallic,
            roughness=self.roughness,
            specular=self.specular,
        )
        create_principled_material.assign_material_to_active_object(mat)
        self.report({"INFO"}, f"Created material '{mat.name}'")
        return {"FINISHED"}


# ── Panel ─────────────────────────────────────────────────────────────────────


class MATERIAL_PT_Panel(bpy.types.Panel):
    """Material utilities panel in the 3D Viewport sidebar"""

    bl_label = "Material Utilities"
    bl_idname = "MATERIAL_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blender Scripts"

    def draw(self, context):
        layout = self.layout
        layout.operator("material.create_principled", icon="MATERIAL")


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    MATERIAL_OT_CreatePrincipled,
    MATERIAL_PT_Panel,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
