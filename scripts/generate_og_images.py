#!/usr/bin/env python3
"""
Generate Open Graph preview images for each game in GamersPaperData.

Each image is a 1200x630 branded card with:
- Dark gradient background
- Game name (large)
- Designer and publisher (smaller)
- Player count and play time (chips)
- GamersPaper branding
- Optional box art overlay (if files/{game_id}/cover.jpg exists)

Output: files/{game_id}/og.png

Usage:
    python3 scripts/generate_og_images.py
"""

import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Constants ───────────────────────────────────────────────────
WIDTH = 1200
HEIGHT = 630
BG_COLOR_TOP = (26, 26, 46)      # #1a1a2e
BG_COLOR_BOTTOM = (16, 16, 32)   # #101020
ACCENT = (99, 102, 241)           # #6366f1 (indigo)
ACCENT_DIM = (60, 62, 140)
TEXT_WHITE = (255, 255, 255)
TEXT_LIGHT = (200, 200, 220)
TEXT_MID = (160, 160, 180)
TEXT_DIM = (120, 120, 140)
CHIP_BG = (255, 255, 255, 18)    # subtle white
BRAND_TEXT = "GamersPaper"

REPO_ROOT = Path(__file__).resolve().parent.parent
FILES_DIR = REPO_ROOT / "files"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font, falling back to default if system fonts aren't available."""
    font_candidates = []
    if bold:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    else:
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_gradient(img: Image.Image):
    """Draw a vertical gradient background."""
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_COLOR_TOP[0] * (1 - ratio) + BG_COLOR_BOTTOM[0] * ratio)
        g = int(BG_COLOR_TOP[1] * (1 - ratio) + BG_COLOR_BOTTOM[1] * ratio)
        b = int(BG_COLOR_TOP[2] * (1 - ratio) + BG_COLOR_BOTTOM[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


def draw_accent_bar(draw: ImageDraw.Draw):
    """Draw a thin accent bar at the top."""
    draw.rectangle([(0, 0), (WIDTH, 4)], fill=ACCENT)


def draw_accent_side(draw: ImageDraw.Draw):
    """Draw a subtle vertical accent stripe on the left."""
    draw.rectangle([(0, 0), (4, HEIGHT)], fill=ACCENT)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_chip(draw: ImageDraw.Draw, x: int, y: int, text: str,
              font: ImageFont.FreeTypeFont) -> int:
    """Draw a rounded chip with text, return the width used."""
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad_x, pad_y = 14, 6
    chip_w = text_w + pad_x * 2
    chip_h = text_h + pad_y * 2
    radius = chip_h // 2

    # Draw rounded rectangle
    draw.rounded_rectangle(
        [(x, y), (x + chip_w, y + chip_h)],
        radius=radius,
        fill=(50, 50, 70),
        outline=(70, 70, 100),
        width=1,
    )
    draw.text((x + pad_x, y + pad_y), text, fill=TEXT_LIGHT, font=font)
    return chip_w


def generate_og_image(game_id: str, rules: dict, cover_path: object = None):
    """Generate a single OG image for a game."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw_gradient(img)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = load_font(46, bold=True)
    font_subtitle = load_font(22)
    font_chip = load_font(18)
    font_brand = load_font(20, bold=True)
    font_brand_sub = load_font(14)

    # Layout
    content_x = 60
    content_w = WIDTH - 120  # max text width

    # If cover image exists, place it on the right and constrain text
    cover_region_w = 0
    if cover_path and cover_path.exists():
        try:
            raw_cover = Image.open(cover_path)
            has_transparency = (raw_cover.mode == "RGBA" and raw_cover.getextrema()[3][0] < 255)
            cover = raw_cover.convert("RGBA")
            # Fit cover into right portion: 300px wide, full height with padding
            cover_w = 280
            cover_h = HEIGHT - 80
            cover.thumbnail((cover_w, cover_h), Image.LANCZOS)
            cover_x = WIDTH - cover.width - 50
            cover_y = (HEIGHT - cover.height) // 2
            # Composite with alpha mask for transparent covers
            img.paste(cover, (cover_x, cover_y), cover)
            # Draw a rounded border for opaque covers to frame them
            if not has_transparency:
                draw.rounded_rectangle(
                    [(cover_x - 2, cover_y - 2),
                     (cover_x + cover.width + 1, cover_y + cover.height + 1)],
                    radius=6,
                    outline=(70, 70, 100),
                    width=2,
                )
            cover_region_w = cover.width + 80
            content_w = WIDTH - 120 - cover_region_w
        except Exception:
            pass  # Skip cover on error

    # Accent elements
    draw_accent_bar(draw)
    draw_accent_side(draw)

    # ── Game title ──
    game_name = rules.get("game_name", game_id.replace("_", " ").title())
    title_lines = wrap_text(game_name, font_title, content_w)
    y = 50
    for line in title_lines[:2]:  # Max 2 lines
        draw.text((content_x, y), line, fill=TEXT_WHITE, font=font_title)
        bbox = font_title.getbbox(line)
        y += bbox[3] - bbox[1] + 8

    # ── Accent underline below title ──
    y += 8
    draw.rectangle([(content_x, y), (content_x + 80, y + 3)], fill=ACCENT)
    y += 20

    # ── Designer + Publisher ──
    designer = rules.get("designer", "")
    publisher = rules.get("publisher", "")
    if designer:
        by_text = f"by {designer}"
        by_lines = wrap_text(by_text, font_subtitle, content_w)
        for line in by_lines[:1]:
            draw.text((content_x, y), line, fill=TEXT_LIGHT, font=font_subtitle)
            bbox = font_subtitle.getbbox(line)
            y += bbox[3] - bbox[1] + 4
    if publisher:
        draw.text((content_x, y), publisher, fill=TEXT_MID, font=font_subtitle)
        bbox = font_subtitle.getbbox(publisher)
        y += bbox[3] - bbox[1] + 4
    y += 16

    # ── Info chips (player count, play time) ──
    chip_x = content_x
    min_p = rules.get("min_players")
    max_p = rules.get("max_players")
    if min_p is not None and max_p is not None:
        player_text = f"{min_p}-{max_p} Players" if min_p != max_p else f"{min_p} Player"
        w = draw_chip(draw, chip_x, y, player_text, font_chip)
        chip_x += w + 10

    play_time = rules.get("play_time_minutes")
    if play_time:
        w = draw_chip(draw, chip_x, y, f"{play_time} min", font_chip)
        chip_x += w + 10

    # ── Overview text (truncated) ──
    overview = rules.get("game_overview", rules.get("objective", ""))
    if overview:
        y += 50
        overview_lines = wrap_text(overview, font_chip, content_w)
        for line in overview_lines[:3]:  # Max 3 lines
            draw.text((content_x, y), line, fill=TEXT_DIM, font=font_chip)
            bbox = font_chip.getbbox(line)
            y += bbox[3] - bbox[1] + 4

    # ── Brand footer ──
    brand_y = HEIGHT - 55
    draw.rectangle([(0, brand_y - 15), (WIDTH, HEIGHT)], fill=(16, 16, 28))
    draw.rectangle([(0, brand_y - 15), (WIDTH, brand_y - 14)], fill=(40, 40, 60))
    draw.text((content_x, brand_y), BRAND_TEXT, fill=ACCENT, font=font_brand)
    bbox = font_brand.getbbox(BRAND_TEXT)
    brand_w = bbox[2] - bbox[0]
    draw.text(
        (content_x + brand_w + 12, brand_y + 4),
        "Board Game Rules Reference",
        fill=TEXT_DIM, font=font_brand_sub,
    )

    # ── Save ──
    out_path = FILES_DIR / game_id / "og.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), "PNG", optimize=True)
    print(f"  Generated: {out_path}")


def validate_cover(cover_path, game_id):
    """Check cover image for white/light background MARGINS (not art that is light).
    Detects uniform white padding around the image by checking if the outermost
    rows/columns are mostly the same light color — a sign of uncropped margins.
    Returns list of warnings. Fails the build if issues are found."""
    warnings = []
    img = Image.open(cover_path).convert("RGB")
    w, h = img.size
    pixels = img.load()

    def is_near_white(r, g, b):
        return r > 230 and g > 230 and b > 230

    # Check each edge: what % of the outermost 3px band is near-white?
    edges = {"top": [], "bottom": [], "left": [], "right": []}
    for x in range(w):
        for dy in range(min(3, h)):
            edges["top"].append(pixels[x, dy])
            edges["bottom"].append(pixels[x, h - 1 - dy])
    for y in range(h):
        for dx in range(min(3, w)):
            edges["left"].append(pixels[dx, y])
            edges["right"].append(pixels[w - 1 - dx, y])

    white_edges = []
    for side, pxs in edges.items():
        white_pct = sum(1 for r, g, b in pxs if is_near_white(r, g, b)) / len(pxs) * 100
        if white_pct > 80:
            white_edges.append(side)

    # Only warn if 2+ edges are white margins (a single light edge could be art)
    if len(white_edges) >= 2:
        warnings.append(
            f"  WARNING: {game_id} cover has white margins on {', '.join(white_edges)} edges. "
            f"Replace with tightly-cropped flat art or a transparent PNG."
        )
    return warnings


def main():
    # Load all games: bundled files + registry
    games = {}

    # Scan files/ directories for rules JSON
    if FILES_DIR.exists():
        for game_dir in sorted(FILES_DIR.iterdir()):
            if not game_dir.is_dir():
                continue
            game_id = game_dir.name
            rules_file = game_dir / f"{game_id}_rules.json"
            if rules_file.exists():
                try:
                    with open(rules_file, "r", encoding="utf-8") as f:
                        games[game_id] = json.load(f)
                except Exception as e:
                    print(f"  Warning: Could not parse {rules_file}: {e}")

    if not games:
        print("No games found in files/")
        sys.exit(1)

    print(f"Generating OG images for {len(games)} games...")
    all_warnings = []
    for game_id, rules in sorted(games.items()):
        # Check for optional cover image (prefer PNG with transparency)
        cover = FILES_DIR / game_id / "cover.png"
        if not cover.exists():
            cover = FILES_DIR / game_id / "cover.jpg"
        if not cover.exists():
            cover = None

        # Validate cover before generating
        if cover and cover.exists():
            all_warnings.extend(validate_cover(cover, game_id))

        generate_og_image(game_id, rules, cover)

    if all_warnings:
        print("\n*** COVER IMAGE ISSUES ***")
        for w in all_warnings:
            print(w)
        print("Fix these before merging — light edges look bad on the dark OG card.")
        sys.exit(1)

    print(f"Done! Generated {len(games)} OG images.")


if __name__ == "__main__":
    main()
