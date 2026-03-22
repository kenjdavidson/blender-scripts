"""
Render Settings Preset
=======================
Applies a set of common render settings (engine, resolution, samples,
output path, etc.) to the current scene in one go.  Edit the presets
dict at the bottom to match your workflow.

Usage:
    Run from Blender's Scripting workspace or Text Editor.
"""

import bpy
import os


def apply_render_preset(
    engine="CYCLES",
    resolution_x=1920,
    resolution_y=1080,
    resolution_percentage=100,
    samples=128,
    use_denoising=True,
    output_path="//renders/",
    file_format="PNG",
    color_mode="RGBA",
    color_depth="16",
    use_transparent=False,
):
    """Apply render settings to the current scene.

    Args:
        engine: Render engine – "CYCLES" or "BLENDER_EEVEE".
        resolution_x: Horizontal resolution in pixels.
        resolution_y: Vertical resolution in pixels.
        resolution_percentage: Render percentage (1–100).
        samples: Number of render samples (Cycles only).
        use_denoising: Enable denoising compositing node (Cycles only).
        output_path: Output directory path (use '//' for relative to .blend).
        file_format: Image file format – "PNG", "JPEG", "OPEN_EXR", etc.
        color_mode: "RGB" or "RGBA".
        color_depth: Bit depth string – "8", "16", "32" (format-dependent).
        use_transparent: Render background as transparent.
    """
    scene = bpy.context.scene
    render = scene.render
    cycles = scene.cycles if hasattr(scene, "cycles") else None

    # Engine
    render.engine = engine

    # Resolution
    render.resolution_x = resolution_x
    render.resolution_y = resolution_y
    render.resolution_percentage = resolution_percentage

    # Samples / denoising (Cycles)
    if engine == "CYCLES" and cycles is not None:
        cycles.samples = samples
        cycles.use_denoising = use_denoising

    # Output
    render.filepath = output_path
    render.image_settings.file_format = file_format
    render.image_settings.color_mode = color_mode
    render.film_transparent = use_transparent

    # Color depth (not supported by all formats)
    try:
        render.image_settings.color_depth = color_depth
    except TypeError:
        pass  # Format does not support this option

    print(
        f"Render preset applied: {engine} | {resolution_x}×{resolution_y} "
        f"@ {resolution_percentage}% | {samples} samples → {output_path}"
    )


# ── Presets ───────────────────────────────────────────────────────────────────

PRESETS = {
    "draft": dict(
        engine="CYCLES",
        resolution_x=1280,
        resolution_y=720,
        resolution_percentage=50,
        samples=32,
        use_denoising=True,
        output_path="//renders/draft/",
    ),
    "final": dict(
        engine="CYCLES",
        resolution_x=1920,
        resolution_y=1080,
        resolution_percentage=100,
        samples=512,
        use_denoising=True,
        output_path="//renders/final/",
        color_depth="16",
    ),
    "eevee_preview": dict(
        engine="BLENDER_EEVEE",
        resolution_x=1920,
        resolution_y=1080,
        resolution_percentage=100,
        samples=64,
        output_path="//renders/eevee/",
    ),
}


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    apply_render_preset(**PRESETS["draft"])
