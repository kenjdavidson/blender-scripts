"""
Set Keyframe Interpolation
===========================
Changes the interpolation mode for all (or selected) keyframes on the
active object's F-Curves.  Useful for quickly switching between BEZIER,
LINEAR, CONSTANT, etc. across an entire animation.

Usage:
    Select the object whose keyframes you want to modify, then run from
    Blender's Scripting workspace or Text Editor.
"""

import bpy

# Supported interpolation modes (subset of bpy.types.Keyframe.interpolation)
INTERPOLATION_MODES = {
    "BEZIER",
    "LINEAR",
    "CONSTANT",
    "BOUNCE",
    "ELASTIC",
    "BACK",
    "EXPO",
    "CIRC",
    "QUAD",
    "CUBIC",
    "QUART",
    "QUINT",
    "SINE",
}


def set_keyframe_interpolation(
    interpolation="BEZIER",
    selected_only=False,
    data_path_filter=None,
):
    """Change keyframe interpolation on the active object's animation data.

    Args:
        interpolation: Target interpolation mode (see INTERPOLATION_MODES).
        selected_only: If True, only modify selected keyframes.
        data_path_filter: Optional string; if provided, only modify F-Curves
                          whose data_path contains this substring
                          (e.g. "location", "rotation_euler").

    Returns:
        Number of keyframes modified.
    """
    if interpolation not in INTERPOLATION_MODES:
        raise ValueError(
            f"Invalid interpolation '{interpolation}'. "
            f"Choose from: {sorted(INTERPOLATION_MODES)}"
        )

    obj = bpy.context.active_object
    if obj is None or obj.animation_data is None or obj.animation_data.action is None:
        print("Active object has no animation data.")
        return 0

    count = 0
    for fcurve in obj.animation_data.action.fcurves:
        if data_path_filter and data_path_filter not in fcurve.data_path:
            continue

        for kf in fcurve.keyframe_points:
            if selected_only and not kf.select_control_point:
                continue
            kf.interpolation = interpolation
            count += 1

    # Refresh the graph editor
    for area in bpy.context.screen.areas:
        if area.type == "GRAPH_EDITOR":
            area.tag_redraw()

    print(
        f"Set {count} keyframe(s) on '{obj.name}' to '{interpolation}' interpolation."
    )
    return count


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    set_keyframe_interpolation(
        interpolation="LINEAR",
        selected_only=False,
    )
