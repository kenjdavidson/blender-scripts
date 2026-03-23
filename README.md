# blender-scripts

Random Blender Python scripts to help with various projects.  
Manage them with Git so changes are always in sync between machines.

---

## Repository layout

Each category under `scripts/` is a self-contained **Blender addon package**.
It can be installed directly into Blender (for the N-panel UI) or run
file-by-file from the Scripting workspace.

```
scripts/
  animation/            # Keyframe, timeline, and NLA helpers
    __init__.py         #   ← addon entry point (bl_info, Operators, Panel)
    set_keyframe_interpolation.py
  geometry/             # Mesh creation and manipulation utilities
    __init__.py
    add_grid_of_objects.py
  golf/                 # 3D-printable golf commemorative plaque generator
    __init__.py
    geometry_utils.py
    ui_panel.py
  materials/            # Material and shader node setup helpers
    __init__.py
    create_principled_material.py
  utilities/            # Scene-wide helpers (renaming, render settings, …)
    __init__.py
    batch_rename_objects.py
    render_settings_preset.py
```

---

## Getting started

### Clone (first time)

```bash
git clone https://github.com/kenjdavidson/blender-scripts.git
```

### Sync changes between machines

```bash
# Pull the latest scripts on whichever machine you sit down at
git pull

# After editing or adding scripts, push them back
git add .
git commit -m "Add/update <script name>"
git push
```

---

## Using the scripts in Blender

### Option A – Install as an addon (recommended)

Each category folder is a valid Blender addon.  Install one or more to get
a panel in the **N-panel** (press `N` in the 3D Viewport) under the
**"Blender Scripts"** tab.

**Step 1 – create a zip of the category folder:**

```bash
# From the repo root – zip each category you want to install
cd scripts
zip -r animation.zip  animation/
zip -r geometry.zip   geometry/
zip -r materials.zip  materials/
zip -r utilities.zip  utilities/
```

**Step 2 – install in Blender:**

1. Open Blender → `Edit > Preferences > Add-ons > Install`.
2. Select the zip file you created.
3. Enable the addon in the list (search by name).

The operators will appear as buttons in `View3D > Sidebar > Blender Scripts`.

> **Tip – keep addons in sync automatically:**  
> Instead of zipping and re-installing, symlink or copy the category folder
> directly into Blender's user addons directory and `git pull` on both
> machines.
>
> | OS      | Addons path |
> |---------|-------------|
> | Windows | `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\` |
> | macOS   | `~/Library/Application Support/Blender/<version>/scripts/addons/` |
> | Linux   | `~/.config/blender/<version>/scripts/addons/` |
>
> ```bash
> # Linux / macOS example – symlink the animation addon
> ln -s ~/blender-scripts/scripts/animation \
>        ~/.config/blender/4.2/scripts/addons/animation_utilities
> ```
>
> After a `git pull` the addon is updated automatically on the next Blender
> launch (or `Edit > Preferences > Add-ons > Refresh`).

### Option B – VSCode Blender Development extension

The [Blender Development extension for VSCode](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)
can run and reload addon packages directly.  Point it at any category folder
(which already contains `__init__.py`) and use **Blender: Start** /
**Blender: Reload Addons** from the command palette.

### Option C – Scripting workspace (one-off run)

1. Open Blender and switch to the **Scripting** workspace.
2. Click **Open** in the Text Editor header and browse to the individual
   `.py` logic file (e.g. `set_keyframe_interpolation.py`).
3. Edit the parameters in the `if __name__ == "__main__":` block if needed.
4. Click **Run Script** (▶) or press **Alt + P**.

---

## Available addons / scripts

### `scripts/animation/` — *Animation Utilities*

| File | Description |
|------|-------------|
| `__init__.py` | Addon entry point – registers the N-panel and operators. |
| `set_keyframe_interpolation.py` | Bulk-change interpolation mode (BEZIER, LINEAR, CONSTANT, …) for all keyframes on the active object. |

### `scripts/geometry/` — *Geometry Utilities*

| File | Description |
|------|-------------|
| `__init__.py` | Addon entry point – registers the N-panel and operators. |
| `add_grid_of_objects.py` | Instantiate an object (or a primitive) in a configurable N×M grid. |

### `scripts/materials/` — *Material Utilities*

| File | Description |
|------|-------------|
| `__init__.py` | Addon entry point – registers the N-panel and operators. |
| `create_principled_material.py` | Create a Principled BSDF material with common properties and assign it to the active object. Compatible with Blender 3.x and 4.x. |

### `scripts/utilities/` — *Scene Utilities*

| File | Description |
|------|-------------|
| `__init__.py` | Addon entry point – registers the N-panel and operators. |
| `batch_rename_objects.py` | Rename all selected (or all scene) objects with a prefix, suffix, and zero-padded index. |
| `render_settings_preset.py` | Apply a named render preset (draft / final / eevee_preview) to the current scene. |

### `scripts/golf/` — *Hole-In-One Commemorative Generator*

| File | Description |
|------|-------------|
| `__init__.py` | Addon entry point – registers `HOLEINONE_Properties`, the Generate operator, and the sidebar panel. |
| `geometry_utils.py` | `COLOR_MAP` configuration, `setup_material`, `sanitize_geometry` (curve→mesh conversion and auto-scaling), and `carve_plaque` (Boolean difference operations). |
| `ui_panel.py` | Sidebar panel in the **Golf** N-panel category with plaque dimension controls and the **Generate 3D Plaque** button. |

#### Hole-In-One workflow

1. **Inkscape** – draw a 100 × 140 mm box named `Rough`, trace course features
   (Green, Sand, Water, Fairway, Tee, Text, …), convert everything to Paths
   (`Path > Object to Path`), and save as **Plain SVG**.
2. **Blender** – import the SVG (`File > Import > Scalable Vector Graphics`).
3. Open the **Golf** tab in the Sidebar (press `N` in the 3D Viewport).
4. Adjust plaque dimensions if needed, then click **Generate 3D Plaque**.

> **Tip – symbolic-link install on Windows:**
> ```
> mklink /D "%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\golf" "PATH_TO_THIS_REPO\scripts\golf"
> ```

---

## Contributing / adding new scripts

1. Create the logic file in the appropriate `scripts/<category>/` folder.
2. Add a module-level docstring explaining what it does, its arguments,
   and how to run it.
3. Guard the standalone entry-point with `if __name__ == "__main__":`.
4. Add a corresponding `Operator` class and a button in the `Panel.draw()`
   method of the category's `__init__.py`.
5. Update the table above.
6. Commit and push.
