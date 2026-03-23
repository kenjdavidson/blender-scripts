# Hole-In-One Commemorative Generator

A Blender Add-on for creating 3D-printable golf course plaques from SVG traces.

## Installation (Development Mode)

To keep the add-on synced with this repository, use a symbolic link:

**Windows** – open Command Prompt as Administrator and run:

```
mklink /D "%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\hole_in_one" "PATH_TO_THIS_REPO\scripts\hole_in_one"
```

**macOS / Linux:**

```bash
ln -s "PATH_TO_THIS_REPO/scripts/hole_in_one" \
      ~/.config/blender/<version>/scripts/addons/hole_in_one
```

After a `git pull` the add-on is updated automatically on the next Blender launch
(or `Edit > Preferences > Add-ons > Refresh`).

## Workflow

1. **Inkscape**
   - Draw a 100 × 140 mm box named `Rough`.
   - Trace course features (Green, Sand, Water, Fairway, Tee, Text, …).
   - Convert all objects to Paths (`Path > Object to Path`).
   - Save as **Plain SVG**.

2. **Blender**
   - Import the SVG (`File > Import > Scalable Vector Graphics`).
   - Open the **Golf** tab in the Sidebar (press `N` in the 3D Viewport).
   - Adjust plaque dimensions if needed.
   - Click **Generate 3D Plaque**.

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Add-on registration, `HOLEINONE_Properties` PropertyGroup, and the Generate operator. |
| `geometry_utils.py` | `COLOR_MAP` configuration, curve-to-mesh conversion, auto-scaling, and Boolean carve logic. |
| `ui_panel.py` | Sidebar panel in the **Golf** N-panel category with plaque dimension controls. |

## Color Map / Layer Depths

Each SVG layer prefix maps to a carve depth (mm from the plaque surface) and a
preview colour:

| Prefix | Depth (mm) | Color |
|--------|-----------|-------|
| Water | 3.0 | Blue |
| Sand | 2.4 | Tan |
| Green | 1.8 | Bright green |
| Tee | 1.8 | Light gray |
| Fairway | 1.2 | Mid green |
| Rough | 0.6 | Dark green |
| Text | 0.0 | White |
