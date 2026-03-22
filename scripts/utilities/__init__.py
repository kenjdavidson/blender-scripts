"""
Scene Utilities – Blender Addon
=================================
Entry point for the Scene Utilities addon.  Registers Blender Operators and
an N-panel UI that wrap the helper functions in this package.

Install this addon by zipping the ``utilities/`` folder and installing it via
``Edit > Preferences > Add-ons > Install``, or by copying the folder into
Blender's user addons directory.
"""

bl_info = {
    "name": "Scene Utilities",
    "author": "kenjdavidson",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Blender Scripts",
    "description": "Scene-wide helpers: object renaming and render configuration",
    "category": "Object",
}

import bpy
from . import batch_rename_objects
from . import render_settings_preset

# ── Operators ─────────────────────────────────────────────────────────────────


class UTIL_OT_BatchRenameObjects(bpy.types.Operator):
    """Rename selected (or all scene) objects with a prefix, suffix, and index"""

    bl_idname = "util.batch_rename_objects"
    bl_label = "Batch Rename Objects"
    bl_options = {"REGISTER", "UNDO"}

    prefix: bpy.props.StringProperty(
        name="Prefix",
        description="String prepended to each name",
        default="",
    )
    suffix: bpy.props.StringProperty(
        name="Suffix",
        description="String appended to each name",
        default="",
    )
    base_name: bpy.props.StringProperty(
        name="Base Name",
        description="Core name used between prefix and index",
        default="Object",
    )
    use_index: bpy.props.BoolProperty(
        name="Use Index",
        description="Append a zero-padded index to each name",
        default=True,
    )
    index_padding: bpy.props.IntProperty(
        name="Index Padding",
        description="Number of digits for zero-padding the index",
        default=3,
        min=1,
        max=10,
    )
    selected_only: bpy.props.BoolProperty(
        name="Selected Only",
        description="Rename only selected objects; if disabled, rename all scene objects",
        default=True,
    )

    def execute(self, context):
        renames = batch_rename_objects.batch_rename(
            prefix=self.prefix,
            suffix=self.suffix,
            base_name=self.base_name,
            use_index=self.use_index,
            index_padding=self.index_padding,
            selected_only=self.selected_only,
        )
        self.report({"INFO"}, f"Renamed {len(renames)} object(s)")
        return {"FINISHED"}


class UTIL_OT_ApplyRenderPreset(bpy.types.Operator):
    """Apply a named render preset to the current scene"""

    bl_idname = "util.apply_render_preset"
    bl_label = "Apply Render Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(
        name="Preset",
        description="Render preset to apply",
        items=[
            ("draft", "Draft", "Fast low-res Cycles render for quick previews"),
            ("final", "Final", "Full-resolution high-sample Cycles render"),
            ("eevee_preview", "EEVEE Preview", "Full-resolution EEVEE preview render"),
        ],
        default="draft",
    )

    def execute(self, context):
        preset_settings = render_settings_preset.PRESETS.get(self.preset)
        if preset_settings is None:
            self.report({"ERROR"}, f"Unknown preset: {self.preset}")
            return {"CANCELLED"}
        render_settings_preset.apply_render_preset(**preset_settings)
        self.report({"INFO"}, f"Applied '{self.preset}' render preset")
        return {"FINISHED"}


# ── Panel ─────────────────────────────────────────────────────────────────────


class UTIL_PT_Panel(bpy.types.Panel):
    """Scene utilities panel in the 3D Viewport sidebar"""

    bl_label = "Scene Utilities"
    bl_idname = "UTIL_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blender Scripts"

    def draw(self, context):
        layout = self.layout
        layout.operator("util.batch_rename_objects", icon="SORTALPHA")
        layout.operator("util.apply_render_preset", icon="RENDER_STILL")


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    UTIL_OT_BatchRenameObjects,
    UTIL_OT_ApplyRenderPreset,
    UTIL_PT_Panel,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
