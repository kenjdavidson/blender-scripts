"""
Animation Utilities – Blender Addon
=====================================
Entry point for the Animation Utilities addon.  Registers Blender Operators
and an N-panel UI that wrap the helper functions in this package.

Install this addon by zipping the ``animation/`` folder and installing it via
``Edit > Preferences > Add-ons > Install``, or by copying the folder into
Blender's user addons directory.
"""

bl_info = {
    "name": "Animation Utilities",
    "author": "kenjdavidson",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Blender Scripts",
    "description": "Helpers for keyframe and F-Curve management",
    "category": "Animation",
}

import bpy
from . import set_keyframe_interpolation

# ── Operator ─────────────────────────────────────────────────────────────────

_INTERPOLATION_ITEMS = [
    ("BEZIER", "Bezier", "Smooth bezier spline interpolation"),
    ("LINEAR", "Linear", "Straight line interpolation"),
    ("CONSTANT", "Constant", "No interpolation – step changes at each keyframe"),
    ("SINE", "Sinusoidal", "Sinusoidal easing"),
    ("QUAD", "Quadratic", "Quadratic easing"),
    ("CUBIC", "Cubic", "Cubic easing"),
    ("QUART", "Quartic", "Quartic easing"),
    ("QUINT", "Quintic", "Quintic easing"),
    ("EXPO", "Exponential", "Exponential easing"),
    ("CIRC", "Circular", "Circular easing"),
    ("BACK", "Back", "Easing with overshoot and recover"),
    ("BOUNCE", "Bounce", "Bounce easing"),
    ("ELASTIC", "Elastic", "Elastic easing"),
]


class ANIM_OT_SetKeyframeInterpolation(bpy.types.Operator):
    """Set keyframe interpolation mode for all F-Curves on the active object"""

    bl_idname = "anim.set_keyframe_interpolation"
    bl_label = "Set Keyframe Interpolation"
    bl_options = {"REGISTER", "UNDO"}

    interpolation: bpy.props.EnumProperty(
        name="Interpolation",
        description="Interpolation mode to apply to keyframes",
        items=_INTERPOLATION_ITEMS,
        default="BEZIER",
    )
    selected_only: bpy.props.BoolProperty(
        name="Selected Only",
        description="Only modify selected keyframes",
        default=False,
    )
    data_path_filter: bpy.props.StringProperty(
        name="Data Path Filter",
        description=(
            "Only modify F-Curves whose data_path contains this string "
            "(e.g. 'location'). Leave empty to affect all."
        ),
        default="",
    )

    def execute(self, context):
        count = set_keyframe_interpolation.set_keyframe_interpolation(
            interpolation=self.interpolation,
            selected_only=self.selected_only,
            data_path_filter=self.data_path_filter or None,
        )
        self.report({"INFO"}, f"Set {count} keyframe(s) to {self.interpolation}")
        return {"FINISHED"}


# ── Panel ─────────────────────────────────────────────────────────────────────


class ANIM_PT_Panel(bpy.types.Panel):
    """Animation utilities panel in the 3D Viewport sidebar"""

    bl_label = "Animation Utilities"
    bl_idname = "ANIM_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blender Scripts"

    def draw(self, context):
        layout = self.layout
        layout.operator("anim.set_keyframe_interpolation", icon="IPO_BEZIER")


# ── Registration ──────────────────────────────────────────────────────────────

_classes = (
    ANIM_OT_SetKeyframeInterpolation,
    ANIM_PT_Panel,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
