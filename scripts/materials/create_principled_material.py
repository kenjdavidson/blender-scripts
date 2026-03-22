"""
Create Principled BSDF Material
================================
Creates a new Principled BSDF material with configurable base color,
metallic, roughness, and other common properties, then assigns it to
the active object.

Usage:
    Run from Blender's Scripting workspace or Text Editor.
"""

import bpy


def create_principled_material(
    name="New Material",
    base_color=(0.8, 0.2, 0.2, 1.0),
    metallic=0.0,
    roughness=0.5,
    specular=0.5,
):
    """Create a Principled BSDF material and return it.

    Args:
        name: Name for the new material.
        base_color: RGBA tuple for the base color (values 0.0–1.0).
        metallic: Metallic factor (0.0 = non-metal, 1.0 = fully metallic).
        roughness: Surface roughness (0.0 = mirror, 1.0 = fully diffuse).
        specular: Specular intensity.

    Returns:
        The newly created bpy.types.Material.
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    nodes.clear()

    # Add Principled BSDF node
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    # "Specular IOR Level" (Blender 4.x) was called "Specular" in Blender 3.x
    specular_input = bsdf.inputs.get("Specular IOR Level") or bsdf.inputs.get("Specular")
    if specular_input:
        specular_input.default_value = specular

    # Add Material Output node
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)

    # Link BSDF to Output
    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat


def assign_material_to_active_object(mat):
    """Assign a material to the currently active object.

    Args:
        mat: A bpy.types.Material to assign.
    """
    obj = bpy.context.active_object
    if obj is None:
        print("No active object selected.")
        return

    if obj.data is None or not hasattr(obj.data, "materials"):
        print(f"Object '{obj.name}' does not support materials.")
        return

    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat

    print(f"Assigned material '{mat.name}' to '{obj.name}'.")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    material = create_principled_material(
        name="Demo Red Metal",
        base_color=(0.8, 0.1, 0.1, 1.0),
        metallic=0.8,
        roughness=0.3,
    )
    assign_material_to_active_object(material)
