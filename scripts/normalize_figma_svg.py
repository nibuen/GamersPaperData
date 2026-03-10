#!/usr/bin/env python3
"""
Normalize SVGs exported from Figma to match the GamersPaperData icon format.

Target format:
  - viewBox="-40 -40 80 80" width="80" height="80"
  - xmlns="http://www.w3.org/2000/svg"
  - White fill (#FFFFFF), no stroke
  - Single path or minimal paths wrapped in a <g> element
  - No Figma-specific metadata, comments, or extra attributes

Usage:
  python normalize_figma_svg.py icon.svg
  python normalize_figma_svg.py *.svg
  python normalize_figma_svg.py --output ../icons/ my_icon.svg
  python normalize_figma_svg.py --dir exports/ --output ../icons/
  python normalize_figma_svg.py --dry-run icon.svg
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Target coordinate system
TARGET_VIEWBOX = "-40 -40 80 80"
TARGET_WIDTH = "80"
TARGET_HEIGHT = "80"
TARGET_FILL = "#FFFFFF"
TARGET_STROKE = "none"

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Register namespaces so ET doesn't mangle them
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def parse_viewbox(vb_str):
    """Parse a viewBox string into (min_x, min_y, width, height)."""
    parts = re.split(r"[,\s]+", vb_str.strip())
    if len(parts) != 4:
        raise ValueError(f"Invalid viewBox: {vb_str!r}")
    return tuple(float(p) for p in parts)


def compute_transform(src_vb, target_vb=(-40, -40, 80, 80)):
    """
    Compute an SVG transform string that maps from source viewBox coordinates
    to target viewBox coordinates.

    Returns the transform attribute string, or None if no transform needed.
    """
    src_x, src_y, src_w, src_h = src_vb
    tgt_x, tgt_y, tgt_w, tgt_h = target_vb

    # Scale factors
    sx = tgt_w / src_w if src_w != 0 else 1
    sy = tgt_h / src_h if src_h != 0 else 1

    # Use uniform scale to preserve aspect ratio
    scale = min(sx, sy)

    # Center of source content in source coords
    src_cx = src_x + src_w / 2
    src_cy = src_y + src_h / 2

    # Center of target
    tgt_cx = tgt_x + tgt_w / 2
    tgt_cy = tgt_y + tgt_h / 2

    # Check if transform is identity (or close enough)
    if (abs(scale - 1.0) < 1e-6
            and abs(src_cx - tgt_cx) < 1e-6
            and abs(src_cy - tgt_cy) < 1e-6):
        return None

    # Build transform: translate to target center, scale, translate from source center
    # Combined: translate(tgt_cx, tgt_cy) scale(s) translate(-src_cx, -src_cy)
    # Which simplifies to: matrix(s, 0, 0, s, tgt_cx - s*src_cx, tgt_cy - s*src_cy)
    tx = tgt_cx - scale * src_cx
    ty = tgt_cy - scale * src_cy

    # Use translate+scale form for readability
    if abs(tx) < 1e-6 and abs(ty) < 1e-6:
        if abs(scale - 1.0) < 1e-6:
            return None
        return f"scale({scale:.6g})"
    elif abs(scale - 1.0) < 1e-6:
        return f"translate({tx:.6g},{ty:.6g})"
    else:
        return f"translate({tx:.6g},{ty:.6g}) scale({scale:.6g})"


def strip_ns(tag):
    """Remove namespace URI from a tag name."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def tag_with_ns(local_name, ns=SVG_NS):
    """Create a namespaced tag."""
    return f"{{{ns}}}{local_name}"


def collect_paths(elem):
    """Recursively collect all <path> elements from an element tree."""
    paths = []
    if strip_ns(elem.tag) == "path":
        paths.append(elem)
    for child in elem:
        paths.extend(collect_paths(child))
    return paths


def collect_circles_rects(elem):
    """Recursively collect <circle>, <ellipse>, <rect>, <polygon>, <polyline>, <line> elements."""
    shapes = []
    shape_tags = {"circle", "ellipse", "rect", "polygon", "polyline", "line"}
    if strip_ns(elem.tag) in shape_tags:
        shapes.append(elem)
    for child in elem:
        shapes.extend(collect_circles_rects(child))
    return shapes


def is_figma_attribute(attr_name):
    """Check if an attribute is Figma-specific metadata."""
    figma_prefixes = ("data-", "figma:")
    figma_attrs = {
        "class", "id", "style",
        "sketch:type", "inkscape:label", "sodipodi:nodetypes",
    }
    attr_local = strip_ns(attr_name)
    if any(attr_local.startswith(p) for p in figma_prefixes):
        return True
    if attr_local in figma_attrs:
        return True
    return False


def normalize_svg(svg_path, dry_run=False):
    """
    Normalize a single SVG file to match the target icon format.

    Returns a dict describing changes made, or None if the file was skipped.
    """
    changes = []
    svg_path = Path(svg_path)

    if not svg_path.exists():
        return {"file": str(svg_path), "error": "File not found", "changes": []}
    if svg_path.suffix.lower() != ".svg":
        return {"file": str(svg_path), "error": "Not an SVG file", "changes": []}

    # Read raw content to handle comments and processing instructions
    raw_content = svg_path.read_text(encoding="utf-8")

    # Strip XML comments (Figma sometimes adds these)
    comment_count = len(re.findall(r"<!--.*?-->", raw_content, re.DOTALL))
    if comment_count:
        raw_content = re.sub(r"<!--.*?-->", "", raw_content, flags=re.DOTALL)
        changes.append(f"Removed {comment_count} XML comment(s)")

    # Strip XML processing instructions (<?xml ... ?>)
    if "<?xml" in raw_content:
        raw_content = re.sub(r"<\?xml[^?]*\?>", "", raw_content)
        changes.append("Removed XML declaration")

    # Parse the SVG
    try:
        root = ET.fromstring(raw_content)
    except ET.ParseError as e:
        return {"file": str(svg_path), "error": f"Parse error: {e}", "changes": []}

    if strip_ns(root.tag) != "svg":
        return {"file": str(svg_path), "error": "Root element is not <svg>", "changes": []}

    # --- Determine source viewBox ---
    src_viewbox_str = root.get("viewBox") or root.get("viewbox")
    src_width = root.get("width", "").replace("px", "").strip()
    src_height = root.get("height", "").replace("px", "").strip()

    if src_viewbox_str:
        src_vb = parse_viewbox(src_viewbox_str)
    elif src_width and src_height:
        try:
            w, h = float(src_width), float(src_height)
            src_vb = (0, 0, w, h)
            changes.append(f"Inferred viewBox from width/height: 0 0 {w} {h}")
        except ValueError:
            src_vb = (0, 0, 80, 80)
            changes.append("Could not parse width/height, assuming 0 0 80 80")
    else:
        src_vb = (0, 0, 80, 80)
        changes.append("No viewBox found, assuming 0 0 80 80")

    # --- Remove <defs>, <style>, <clipPath>, <mask>, <filter>, <linearGradient>,
    #     <radialGradient>, <pattern> elements ---
    remove_tags = {
        "defs", "style", "clipPath", "mask", "filter",
        "linearGradient", "radialGradient", "pattern", "metadata",
        "title", "desc", "foreignObject",
    }

    def remove_elements(parent):
        """Remove unwanted elements recursively. Returns count removed."""
        removed = 0
        to_remove = []
        for child in parent:
            local_tag = strip_ns(child.tag)
            if local_tag in remove_tags:
                to_remove.append(child)
            else:
                removed += remove_elements(child)
        for child in to_remove:
            parent.remove(child)
            removed += 1
        return removed

    removed_count = remove_elements(root)
    if removed_count:
        changes.append(f"Removed {removed_count} unwanted element(s) (defs, style, clipPath, etc.)")

    # --- Collect all path elements ---
    all_paths = collect_paths(root)
    all_shapes = collect_circles_rects(root)

    if not all_paths and not all_shapes:
        return {
            "file": str(svg_path),
            "error": "No <path> or shape elements found after cleanup",
            "changes": changes,
        }

    # --- Strip Figma-specific attributes from paths ---
    figma_attrs_removed = 0
    for path in all_paths + all_shapes:
        to_remove = [a for a in path.attrib if is_figma_attribute(a)]
        for a in to_remove:
            del path.attrib[a]
            figma_attrs_removed += 1

        # Also strip clip-path, mask, filter references
        for ref_attr in ("clip-path", "mask", "filter"):
            if ref_attr in path.attrib:
                del path.attrib[ref_attr]
                figma_attrs_removed += 1

    if figma_attrs_removed:
        changes.append(f"Removed {figma_attrs_removed} Figma/unwanted attribute(s) from paths")

    # --- Set fill and stroke on all paths ---
    # Black fills become transparent (none), all other fills become white
    BLACK_COLORS = {"black", "#000", "#000000", "#0000", "rgb(0,0,0)", "rgb(0, 0, 0)"}
    TRANSPARENT_COLORS = {"none", "transparent", ""}

    fill_changes = 0
    for path in all_paths + all_shapes:
        old_fill = path.get("fill", "").strip().lower()
        old_stroke = path.get("stroke", "")

        if old_fill in BLACK_COLORS:
            target_fill = "none"
        elif old_fill in TRANSPARENT_COLORS:
            target_fill = "none"
        else:
            target_fill = TARGET_FILL

        if old_fill != target_fill.lower():
            fill_changes += 1
        if old_stroke.lower() != TARGET_STROKE.lower():
            fill_changes += 1

        path.set("fill", target_fill)
        path.set("stroke", TARGET_STROKE)

        # Remove stroke-related attributes
        for attr in list(path.attrib):
            local = strip_ns(attr)
            if local.startswith("stroke-") and local != "stroke":
                del path.attrib[attr]

        # Remove fill-rule, fill-opacity, opacity if fully opaque
        for attr in ("fill-rule", "fill-opacity", "opacity", "stroke-width",
                      "stroke-linecap", "stroke-linejoin", "stroke-miterlimit",
                      "stroke-dasharray", "stroke-dashoffset", "stroke-opacity"):
            if attr in path.attrib:
                del path.attrib[attr]

    if fill_changes:
        changes.append(f"Updated fill/stroke on {fill_changes} attribute(s)")

    # --- Compute transform if viewBox differs ---
    transform_str = compute_transform(src_vb)

    if transform_str:
        changes.append(
            f"viewBox {src_viewbox_str or 'inferred'} -> {TARGET_VIEWBOX} "
            f"(transform: {transform_str})"
        )

    # --- Build the output SVG ---
    # We build it manually for clean output matching the target format exactly
    lines = []
    lines.append(
        f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" '
        f'viewBox="{TARGET_VIEWBOX}" width="{TARGET_WIDTH}" height="{TARGET_HEIGHT}">'
    )
    lines.append("  <defs/>")

    # Wrap all paths in a <g> element, with optional transform
    if transform_str:
        lines.append(f'  <g transform="{transform_str}">')
    else:
        lines.append("  <g>")

    for path in all_paths:
        # Build path element string
        d = path.get("d", "")
        if not d:
            continue
        # Use the fill set during normalization (white or none)
        path_fill = path.get("fill", TARGET_FILL)
        attrs = f'stroke="{TARGET_STROKE}" fill="{path_fill}" d="{d}"'
        lines.append(f"    <path {attrs}/>")

    # Handle basic shapes (convert to the output as-is with fill/stroke)
    for shape in all_shapes:
        local_tag = strip_ns(shape.tag)
        # Rebuild with only geometric attributes + fill/stroke
        geom_attrs = {
            "circle": ("cx", "cy", "r"),
            "ellipse": ("cx", "cy", "rx", "ry"),
            "rect": ("x", "y", "width", "height", "rx", "ry"),
            "polygon": ("points",),
            "polyline": ("points",),
            "line": ("x1", "y1", "x2", "y2"),
        }
        # Use the fill set during normalization (white or none)
        shape_fill = shape.get("fill", TARGET_FILL)
        attr_parts = [f'stroke="{TARGET_STROKE}"', f'fill="{shape_fill}"']
        for attr_name in geom_attrs.get(local_tag, ()):
            val = shape.get(attr_name)
            if val is not None:
                attr_parts.append(f'{attr_name}="{val}"')
        lines.append(f'    <{local_tag} {" ".join(attr_parts)}/>')

    lines.append("  </g>")
    lines.append("</svg>")
    lines.append("")  # trailing newline

    output_content = "\n".join(lines)

    if not dry_run:
        svg_path.write_text(output_content, encoding="utf-8")

    # Summarize viewBox change
    if src_viewbox_str and src_viewbox_str.strip() != TARGET_VIEWBOX:
        changes.append(f"viewBox: {src_viewbox_str.strip()} -> {TARGET_VIEWBOX}")
    elif not src_viewbox_str:
        changes.append(f"viewBox: (none) -> {TARGET_VIEWBOX}")

    changes.append(f"Paths: {len(all_paths)}, Shapes: {len(all_shapes)}")

    return {
        "file": str(svg_path),
        "error": None,
        "changes": changes,
        "dry_run": dry_run,
    }


def gather_svg_files(args):
    """Collect all SVG file paths from arguments."""
    files = []

    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.is_dir():
            print(f"Error: --dir {args.dir} is not a directory", file=sys.stderr)
            sys.exit(1)
        files.extend(sorted(dir_path.glob("*.svg")))

    for f in (args.files or []):
        p = Path(f)
        if p.is_dir():
            files.extend(sorted(p.glob("*.svg")))
        else:
            files.append(p)

    return files


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Figma-exported SVGs to GamersPaperData icon format."
    )
    parser.add_argument(
        "files", nargs="*", help="SVG file(s) to normalize"
    )
    parser.add_argument(
        "--dir", "-d", help="Directory of SVG files to normalize"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory (default: overwrite in place)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without writing files"
    )

    args = parser.parse_args()

    if not args.files and not args.dir:
        parser.print_help()
        sys.exit(1)

    files = gather_svg_files(args)

    if not files:
        print("No SVG files found.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output) if args.output else None
    if output_dir and not output_dir.exists():
        if not args.dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created output directory: {output_dir}")

    success_count = 0
    error_count = 0

    for svg_file in files:
        # If output dir specified, copy to that dir
        if output_dir:
            target_path = output_dir / svg_file.name
        else:
            target_path = svg_file

        # For output dir mode, we read from source but write to target
        # Copy source to target first if different paths, then normalize in place
        if output_dir and svg_file != target_path:
            if not args.dry_run:
                target_path.write_text(
                    svg_file.read_text(encoding="utf-8"), encoding="utf-8"
                )
            work_path = target_path
        else:
            work_path = svg_file

        result = normalize_svg(work_path, dry_run=args.dry_run)

        prefix = "[DRY RUN] " if args.dry_run else ""

        if result.get("error") and not result.get("changes"):
            print(f"{prefix}ERROR {result['file']}: {result['error']}")
            error_count += 1
        else:
            status = "OK" if not result.get("error") else f"WARN ({result['error']})"
            print(f"{prefix}{status} {result['file']}")
            for change in result.get("changes", []):
                print(f"  - {change}")
            success_count += 1

    print()
    print(f"Summary: {success_count} file(s) processed, {error_count} error(s)")
    if args.dry_run:
        print("(dry run -- no files were modified)")


if __name__ == "__main__":
    main()
