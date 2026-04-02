"""Insert-layer construction pipeline for the golf plaque generator.

Builds a set of printable **insert pieces** from SVG golf-course traces.
Each terrain element (Water, Sand, Green, Tee, Fairway, Rough) becomes a
raised slab that fits into a matching hole in its parent layer:

.. code-block:: text

    Base ← Rough insert (has holes for Fairway, Sand, Green, Tee, Water)
               └── Fairway insert (has holes for Green, Tee, Sand, Water)
                       └── Green  insert  (has holes for Water)
                       └── Tee    insert  (has holes for Water)
                       └── Sand   insert  (has holes for Water)
                               └── Water  insert  (innermost, no holes)

Each insert sits slightly smaller than its receiving hole (controlled by
``props.insert_clearance`` and ``props.use_shrink_element``) so it can be
glued in place to create a multi-colour, raised, layered design.

This pipeline is deliberately separate from :mod:`plaque_builder` so that
the two workflows can evolve independently and can be triggered from distinct
operators or API endpoints.
"""

import bmesh
import bpy

from .collection_utils import (
    clear_collection,
    ensure_cutters_collection,
    ensure_inserts_collection,
    move_object_to_collection,
)
from .config import (
    BASE_OBJECT_NAME,
    COLOR_MAP,
    CUTTER_EPSILON,
    ElementType,
    PLAQUE_BASE_PREFIXES,
    STRAP_HOLE_PREFIXES,
)
from .cutter_pipeline import (
    CUTTER_TOP_POKE_MM,
    cleanup_base_mesh,
    is_valid_cutter_mesh,
)
from .draft_angle import apply_flat_inset, apply_flat_outset
from .element_strategy import BuildContext, get_strategy
from .materials import setup_material
from .svg_utils import find_plaque_base, sanitize_geometry

# Horizontal gap between adjacent insert display objects (mm).
_INSERT_DISPLAY_GAP_MM = 10.0


def _xy_segments_intersect(p1, p2, q1, q2, eps=1e-9):
    """Return True when two XY line segments intersect (including collinear overlap)."""

    def _orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def _on_segment(a, b, c):
        return (
            min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps
            and min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps
        )

    o1 = _orient(p1, p2, q1)
    o2 = _orient(p1, p2, q2)
    o3 = _orient(q1, q2, p1)
    o4 = _orient(q1, q2, p2)

    if (o1 > eps and o2 < -eps or o1 < -eps and o2 > eps) and (
        o3 > eps and o4 < -eps or o3 < -eps and o4 > eps
    ):
        return True

    if abs(o1) <= eps and _on_segment(p1, p2, q1):
        return True
    if abs(o2) <= eps and _on_segment(p1, p2, q2):
        return True
    if abs(o3) <= eps and _on_segment(q1, q2, p1):
        return True
    if abs(o4) <= eps and _on_segment(q1, q2, p2):
        return True
    return False


def _has_xy_self_intersections(obj):
    """Detect non-adjacent edge intersections in a flat XY outline mesh."""
    if obj is None or obj.data is None:
        return False

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    edges = list(bm.edges)
    edge_count = len(edges)
    if edge_count < 4:
        bm.free()
        return False

    intersections_found = False
    for idx_a in range(edge_count):
        edge_a = edges[idx_a]
        a1 = (edge_a.verts[0].co.x, edge_a.verts[0].co.y)
        a2 = (edge_a.verts[1].co.x, edge_a.verts[1].co.y)
        verts_a = {edge_a.verts[0], edge_a.verts[1]}

        for idx_b in range(idx_a + 1, edge_count):
            edge_b = edges[idx_b]
            # Adjacent edges are expected to meet; ignore those pairs.
            if edge_b.verts[0] in verts_a or edge_b.verts[1] in verts_a:
                continue

            b1 = (edge_b.verts[0].co.x, edge_b.verts[0].co.y)
            b2 = (edge_b.verts[1].co.x, edge_b.verts[1].co.y)
            if _xy_segments_intersect(a1, a2, b1, b2):
                intersections_found = True
                break

        if intersections_found:
            break

    bm.free()
    return intersections_found


def _apply_flat_inset_safe(obj, inset_mm):
    """Inset with rollback when the resulting outline self-intersects."""
    if obj is None or obj.data is None or inset_mm <= 0.0:
        return False

    original_coords = [vertex.co.copy() for vertex in obj.data.vertices]
    apply_flat_inset(obj, inset_mm)

    if _has_xy_self_intersections(obj):
        for vertex, original in zip(obj.data.vertices, original_coords):
            vertex.co = original
        obj.data.update()
        return False

    return True


def _find_max_safe_inset(source_obj, target_inset_mm, iterations=12):
    """Return the largest inset <= target that avoids outline self-intersection."""
    if source_obj is None or source_obj.data is None or target_inset_mm <= 0.0:
        return 0.0

    # Fast path: requested clearance already works.
    temp_obj = source_obj.copy()
    temp_obj.data = source_obj.data.copy()
    try:
        if _apply_flat_inset_safe(temp_obj, target_inset_mm):
            return target_inset_mm
    finally:
        if temp_obj.data is not None and temp_obj.data.users == 0:
            bpy.data.meshes.remove(temp_obj.data)

    # Binary search for the largest safe inset.
    low = 0.0
    high = target_inset_mm
    best = 0.0

    for _ in range(max(1, int(iterations))):
        mid = (low + high) * 0.5
        temp_obj = source_obj.copy()
        temp_obj.data = source_obj.data.copy()
        try:
            if _apply_flat_inset_safe(temp_obj, mid):
                best = mid
                low = mid
            else:
                high = mid
        finally:
            if temp_obj.data is not None and temp_obj.data.users == 0:
                bpy.data.meshes.remove(temp_obj.data)

    return best


def _carveable_layers_sorted():
    """Return CARVE-type layers sorted by depth ascending (shallowest / outermost first)."""
    return sorted(
        [
            (prefix, config)
            for prefix, config in COLOR_MAP.items()
            if config.element_type == ElementType.CARVE
        ],
        key=lambda item: item[1].depth,
    )


def _duplicate_mesh_obj(source, name, collection):
    """Return a standalone mesh copy of *source*, linked to *collection*."""
    dup = source.copy()
    if source.data is not None:
        dup.data = source.data.copy()
    dup.name = name
    collection.objects.link(dup)
    return dup


def _apply_solidify_and_bake(obj, thickness, offset=-1.0):
    """Add a Solidify modifier to *obj* and immediately apply it.

    Args:
        obj:       The Blender mesh object to solidify.
        thickness: Solidify thickness in mm.
        offset:    Solidify offset direction (``-1.0`` = extend downward from
                   the original face; ``1.0`` = extend upward).
    """
    if obj.data is None:
        return

    # Remove duplicate boundary vertices and triangulate n-gons before
    # solidify. Imported SVG meshes can contain coincident points and holed
    # n-gons that trigger one-off downward spikes on concave outlines.
    bpy.context.view_layer.objects.active = obj
    weld = obj.modifiers.new(name="Weld", type="WELD")
    weld.merge_threshold = 0.0001
    bpy.ops.object.modifier_apply(modifier=weld.name)

    tri = obj.modifiers.new(name="Triangulate", type="TRIANGULATE")
    tri.quad_method = "BEAUTY"
    tri.ngon_method = "BEAUTY"
    bpy.ops.object.modifier_apply(modifier=tri.name)

    solidify = obj.modifiers.new(name="Solidify", type="SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = offset
    # Even-offset can generate extreme spikes at sharp concave corners.
    solidify.use_even_offset = False
    solidify.use_quality_normals = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solidify.name)


def _boolean_subtract(target, cutter):
    """Apply a Boolean difference from *cutter* into *target*."""
    mod = target.modifiers.new(
        type="BOOLEAN", name=f"InsertCut_{cutter.name}"
    )
    mod.object = cutter
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _cleanup_insert_mesh(obj):
    """Repair common mesh artefacts that can manifest as extrusion spikes."""
    if obj is None or obj.data is None:
        return

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    if not bm.verts:
        bm.free()
        return

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.dissolve_degenerate(bm, dist=0.000001, edges=bm.edges)

    loose_verts = [vertex for vertex in bm.verts if not vertex.link_edges]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

    loose_edges = [edge for edge in bm.edges if not edge.link_faces]
    if loose_edges:
        bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _enforce_insert_z_bounds(obj, min_z, max_z):
    """Clamp insert-vertex Z values to the expected printable band."""
    if obj is None or obj.data is None:
        return

    for vertex in obj.data.vertices:
        if vertex.co.z < min_z:
            vertex.co.z = min_z
        elif vertex.co.z > max_z:
            vertex.co.z = max_z
    obj.data.update()


def _resolve_text_element_type(props):
    """Return EMBOSS/ENGRAVE mode for Text based on user settings."""
    if getattr(props, "text_mode", "EMBOSS") == "ENGRAVE":
        return ElementType.ENGRAVE
    return ElementType.EMBOSS


def _apply_text_to_base(
    props,
    all_svg_objs,
    base,
    plaque_thick,
    base_x,
    base_y,
    inserts_collection,
    cutters_collection,
):
    """Apply Text.* objects to the insert base using emboss/engrave strategies."""
    text_config = COLOR_MAP.get("Text")
    if text_config is None:
        return 0

    text_objs = [obj for obj in all_svg_objs if obj.name.startswith("Text")]
    if not text_objs:
        return 0

    text_material = setup_material("Text", text_config.color)
    ctx = BuildContext(
        base=base,
        plaque_thickness=plaque_thick,
        base_x=base_x,
        base_y=base_y,
        output_collection=inserts_collection,
        cutters_collection=cutters_collection,
    )
    strategy = get_strategy(_resolve_text_element_type(props))
    strategy.process(text_objs, "Text", text_config, props, ctx, text_material)
    return len(text_objs)


def build_inserts(props):
    """Generate printable insert pieces from the imported SVG golf-course layers.

    For each CARVE-type terrain layer present in the scene (Rough, Fairway,
    Green, Tee, Sand, Water) this function produces:

    * A **base plaque** with a receiving hole sized to the outermost terrain
      element's outline.
        * One **insert slab** per terrain element, sized smaller than its receiving
            hole by ``props.insert_clearance``, with receiving pockets cut for every
            deeper / inner terrain element.

    All generated objects are placed in the ``Hole_In_One_Inserts`` collection.

    The layers are processed in the order determined by their ``depth`` value
    in :data:`~config.COLOR_MAP`: shallowest layers (e.g. Rough at 0.6 mm) are
    the outermost pieces; deepest layers (e.g. Water at 3.0 mm) are the
    innermost pieces.  This naturally satisfies the requirement that
    water/hazards always cut through all surrounding elements.

    Args:
        props: A Blender scene property group (``HOLEINONE_InsertProperties``)
               or an :class:`~insert_request.InsertRequest` dataclass instance.
    """
    inserts_collection = ensure_inserts_collection()
    cutters_collection = ensure_cutters_collection()
    clear_collection(inserts_collection)
    clear_collection(cutters_collection)

    element_height = (
        max(1, int(props.insert_element_layers)) * float(props.print_layer_height)
    )
    hole_depth = (
        max(1, int(props.insert_hole_layers)) * float(props.print_layer_height)
    )
    effective_hole_depth = min(hole_depth, element_height)
    clearance = float(max(0.0, props.insert_clearance))
    use_shrink = getattr(props, "use_shrink_element", True)

    # ── Collect and sanitize SVG objects ────────────────────────────────────
    all_known_prefixes = (
        tuple(COLOR_MAP.keys()) + PLAQUE_BASE_PREFIXES + STRAP_HOLE_PREFIXES
    )
    all_svg_objs = [
        obj
        for obj in bpy.data.objects
        if any(obj.name.startswith(pre) for pre in all_known_prefixes)
    ]
    all_svg_objs = sanitize_geometry(all_svg_objs, props, cutters_collection)

    # ── Determine layers present in the SVG ─────────────────────────────────
    ordered_layers = _carveable_layers_sorted()
    present_layers = [
        (prefix, config)
        for prefix, config in ordered_layers
        if any(obj.name.startswith(prefix) for obj in all_svg_objs)
    ]

    source_clearance_map = {}
    if use_shrink and clearance > 0.0:
        adjusted_sources = []
        for prefix, _ in present_layers:
            for source in (obj for obj in all_svg_objs if obj.name.startswith(prefix)):
                safe_clearance = _find_max_safe_inset(source, clearance)
                source_clearance_map[source.name] = safe_clearance
                if safe_clearance + 1e-6 < clearance:
                    adjusted_sources.append((source.name, safe_clearance))

        if adjusted_sources:
            print("[golf_tools] Clearance reduced for invalid inset outlines:")
            for source_name, safe_clearance in sorted(adjusted_sources):
                print(
                    "  -",
                    source_name,
                    "requested=",
                    round(clearance, 4),
                    "applied=",
                    round(safe_clearance, 4),
                )

    if not present_layers:
        print("[golf_tools] No carveable SVG layers found; insert build skipped.")
        return

    # ── Determine plaque dimensions ──────────────────────────────────────────
    plaque_base_svg = find_plaque_base(all_svg_objs)
    if plaque_base_svg is not None:
        base_x = plaque_base_svg.dimensions.x
        base_y = plaque_base_svg.dimensions.y
    else:
        base_x = float(props.plaque_width)
        base_y = float(props.plaque_height)

    plaque_thick = float(props.plaque_thick)

    # ── Build the base plaque with a receiving hole for the outermost layer ─
    bpy.ops.mesh.primitive_cube_add(size=1)
    base = bpy.context.active_object
    base.name = f"{BASE_OBJECT_NAME}_Inserts"
    move_object_to_collection(base, inserts_collection)
    base.scale = (base_x, base_y, plaque_thick)
    bpy.ops.object.transform_apply(scale=True)

    outermost_prefix, _ = present_layers[0]
    outermost_svgs = [
        obj for obj in all_svg_objs if obj.name.startswith(outermost_prefix)
    ]

    for svg_src in outermost_svgs:
        hole_cutter = _duplicate_mesh_obj(
            svg_src,
            f"_InsertBaseHole_{outermost_prefix}",
            cutters_collection,
        )
        if clearance > 0.0 and not use_shrink:
            # Grow base hole only when hole-growth mode is selected.
            apply_flat_outset(hole_cutter, clearance)
        # Position cutter at the top surface of the base and extend downward.
        hole_cutter.location.z = plaque_thick / 2.0 + CUTTER_TOP_POKE_MM
        _apply_solidify_and_bake(
            hole_cutter,
            hole_depth + CUTTER_TOP_POKE_MM + CUTTER_EPSILON,
            offset=-1.0,
        )
        if is_valid_cutter_mesh(hole_cutter):
            _boolean_subtract(base, hole_cutter)
        hole_cutter.display_type = "WIRE"
        hole_cutter.hide_render = True

    # ── Build an insert slab for each terrain layer ──────────────────────────
    # Start display offset to the right of the base plaque.
    display_x_offset = base_x / 2.0 + _INSERT_DISPLAY_GAP_MM

    for layer_index, (prefix, config) in enumerate(present_layers):
        svg_sources = [obj for obj in all_svg_objs if obj.name.startswith(prefix)]
        if not svg_sources:
            continue

        mat = setup_material(prefix, config.color)
        insert_pieces = []
        max_piece_width = 0.0

        for piece_index, svg_src in enumerate(svg_sources):
            insert = _duplicate_mesh_obj(
                svg_src,
                f"Insert_{prefix}_{piece_index:02d}",
                inserts_collection,
            )

            # Apply clearance: shrink the insert so it fits in its parent hole.
            if use_shrink and clearance > 0.0:
                inset_amount = source_clearance_map.get(svg_src.name, clearance)
                if inset_amount > 0.0 and not _apply_flat_inset_safe(insert, inset_amount):
                    # Last-resort numerical fallback: build the piece unshrunk
                    # rather than emitting broken topology.
                    print(
                        "[golf_tools] Inset skipped after safety check for",
                        insert.name,
                        "(requested=",
                        round(inset_amount, 4),
                        ")",
                    )

            # Extrude the flat outline upward to element_height.
            # offset = 1.0 → original face (Z=0) becomes the bottom face;
            # the solidify extends upward.
            _apply_solidify_and_bake(insert, element_height, offset=1.0)
            _cleanup_insert_mesh(insert)
            _enforce_insert_z_bounds(insert, 0.0, element_height)

            if not insert.data.materials:
                insert.data.materials.append(mat)

            # ── Cut receiving pockets for all deeper (inner) elements ─────────
            # Layers are sorted shallowest→deepest so everything after
            # layer_index is geometrically "inside" the current element.
            deeper_layers = present_layers[layer_index + 1 :]
            for inner_prefix, _ in deeper_layers:
                inner_sources = [
                    obj
                    for obj in all_svg_objs
                    if obj.name.startswith(inner_prefix)
                ]
                for inner_index, inner_src in enumerate(inner_sources):
                    inner_cutter = _duplicate_mesh_obj(
                        inner_src,
                        f"_InsertHole_{prefix}_{inner_prefix}_{inner_index:02d}",
                        cutters_collection,
                    )
                    # When growing holes rather than shrinking inserts, expand
                    # the inner cutout so the child insert fits with clearance.
                    if clearance > 0.0 and not use_shrink:
                        apply_flat_outset(inner_cutter, clearance)
                    # Position the cutter above the insert top and cut only a
                    # pocket depth (hole_layers), leaving lower parent layers
                    # intact so stacked elements preserve visible height steps.
                    inner_cutter.location.z = element_height + CUTTER_TOP_POKE_MM
                    _apply_solidify_and_bake(
                        inner_cutter,
                        effective_hole_depth + CUTTER_TOP_POKE_MM + CUTTER_EPSILON,
                        offset=-1.0,
                    )
                    if is_valid_cutter_mesh(inner_cutter):
                        _boolean_subtract(insert, inner_cutter)
                        _cleanup_insert_mesh(insert)
                        _enforce_insert_z_bounds(insert, 0.0, element_height)
                    inner_cutter.display_type = "WIRE"
                    inner_cutter.hide_render = True

            insert_pieces.append(insert)
            if insert.dimensions.x > max_piece_width:
                max_piece_width = insert.dimensions.x

        # ── Offset inserts for display ────────────────────────────────────────
        # Insert mesh data is already centered; advance each layer rightward.
        for insert_piece in insert_pieces:
            insert_piece.location.x += display_x_offset

        display_x_offset += max_piece_width + _INSERT_DISPLAY_GAP_MM

    # Text is not an insert layer. It is always applied on the base using
    # the same emboss/engrave options as the Engrave Builder.
    applied_text_count = _apply_text_to_base(
        props,
        all_svg_objs,
        base,
        plaque_thick,
        base_x,
        base_y,
        inserts_collection,
        cutters_collection,
    )

    cleanup_base_mesh(base)

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    print(
        "[golf_tools] Insert build complete --",
        len(present_layers), "layers,",
        "text_objs=", applied_text_count,
        "text_mode=", getattr(props, "text_mode", "EMBOSS"),
        "element_height=", round(element_height, 3), "mm,",
        "hole_depth=", round(effective_hole_depth, 3), "mm,",
        "clearance=", round(clearance, 3), "mm",
        "(shrink_element=", use_shrink, ")",
    )

