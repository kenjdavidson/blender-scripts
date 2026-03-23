"""
Hole-In-One UI Panel
======================
Defines the Sidebar panel that exposes plaque dimensions and the
"Generate 3D Plaque" button in the **Golf** N-panel category.
"""

import bpy


class HOLEINONE_PT_Panel(bpy.types.Panel):
    """Sidebar panel for the Hole-In-One Commemorative Generator"""

    bl_label = "Hole-In-One Generator"
    bl_idname = "HOLEINONE_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Golf"

    def draw(self, context):
        layout = self.layout
        props = context.scene.golf_props

        col = layout.column(align=True)
        col.label(text="Plaque Dimensions:")
        col.prop(props, "plaque_width")
        col.prop(props, "plaque_height")
        col.prop(props, "plaque_thick")

        layout.separator()
        layout.prop(props, "use_manual_scale")

        layout.separator()
        layout.prop(props, "generate_protective_frame")

        layout.separator()
        layout.operator("object.generate_commemorative", icon="MESH_CUBE")
