"""
Batch Rename Objects
=====================
Renames all selected objects (or all scene objects) with a configurable
prefix, suffix, and optional zero-padded index.

Usage:
    Select the objects you want to rename, then run from Blender's
    Scripting workspace or Text Editor.
"""

import bpy


def batch_rename(
    prefix="",
    suffix="",
    base_name="Object",
    use_index=True,
    index_padding=3,
    selected_only=True,
):
    """Rename objects with a consistent naming scheme.

    Args:
        prefix: String prepended to each name.
        suffix: String appended to each name.
        base_name: Core name used between prefix and index.
        use_index: If True, append a zero-padded index to each name.
        index_padding: Number of digits used for zero-padding the index.
        selected_only: If True, rename only selected objects;
                       otherwise rename all scene objects.

    Returns:
        List of (old_name, new_name) tuples for each renamed object.
    """
    if selected_only:
        objects = [obj for obj in bpy.context.selected_objects]
    else:
        objects = list(bpy.context.scene.objects)

    if not objects:
        print("No objects to rename.")
        return []

    renames = []
    for i, obj in enumerate(objects):
        old_name = obj.name
        if use_index:
            index_str = str(i + 1).zfill(index_padding)
            new_name = f"{prefix}{base_name}_{index_str}{suffix}"
        else:
            new_name = f"{prefix}{base_name}{suffix}"

        obj.name = new_name
        renames.append((old_name, new_name))
        print(f"  '{old_name}' → '{new_name}'")

    print(f"Renamed {len(renames)} object(s).")
    return renames


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    batch_rename(
        prefix="Prop_",
        suffix="",
        base_name="Mesh",
        use_index=True,
        index_padding=3,
        selected_only=True,
    )
