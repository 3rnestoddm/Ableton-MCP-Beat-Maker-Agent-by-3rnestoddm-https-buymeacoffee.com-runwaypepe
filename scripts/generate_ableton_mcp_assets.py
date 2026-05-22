#!/usr/bin/env python3
"""Generate deterministic image assets for the Ableton MCP-only repo."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "ableton-mcp"

INK = (9, 15, 28)
PANEL = (16, 25, 40)
GREEN = (142, 255, 75)
CYAN = (34, 224, 203)
GOLD = (255, 191, 76)
RED = (255, 92, 78)
WHITE = (243, 247, 255)
MUTED = (177, 191, 211)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def gradient(size: tuple[int, int]) -> Image.Image:
    width, height = size
    img = Image.new("RGB", size, INK)
    pix = img.load()
    for y in range(height):
        for x in range(width):
            tx = x / max(1, width - 1)
            ty = y / max(1, height - 1)
            pulse = 0.5 + 0.5 * math.sin((tx * 3.0 + ty * 2.1) * math.pi)
            pix[x, y] = (
                8 + int(18 * ty) + int(18 * pulse * tx),
                16 + int(42 * tx) + int(22 * pulse * (1 - ty)),
                31 + int(32 * ty) + int(20 * tx),
            )
    return img


def draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    for x in range(-80, width + 120, 82):
        draw.line([(x, height), (x + 220, 0)], fill=(255, 255, 255, 22), width=1)
    for y in range(70, height, 78):
        draw.line([(0, y), (width, y + 12)], fill=(255, 255, 255, 16), width=1)


def draw_mcp_nodes(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    rng = random.Random(312)
    nodes: list[tuple[int, int, tuple[int, int, int]]] = []
    for _ in range(28):
        nodes.append(
            (
                rng.randrange(int(width * 0.50), width - 70),
                rng.randrange(90, height - 85),
                rng.choice([GREEN, CYAN, GOLD, RED]),
            )
        )
    for i, (x1, y1, _) in enumerate(nodes):
        for x2, y2, _ in nodes[i + 1 :]:
            dist = math.hypot(x1 - x2, y1 - y2)
            if dist < 210:
                draw.line([(x1, y1), (x2, y2)], fill=CYAN + (72,), width=2)
    for x, y, color in nodes:
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color + (235,))
        draw.ellipse((x - 22, y - 22, x + 22, y + 22), outline=color + (70,), width=2)


def draw_wave(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    mid = (top + bottom) // 2
    points = []
    for i, x in enumerate(range(left, right, 8)):
        t = i / 8
        y = mid + int(math.sin(t * 1.8) * math.sin(t * 0.37) * (bottom - top) * 0.42)
        points.append((x, y))
    draw.line(points, fill=CYAN + (230,), width=6, joint="curve")
    draw.line(points, fill=WHITE + (110,), width=2, joint="curve")


def tag(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color: tuple[int, int, int]) -> int:
    fnt = font(30, bold=True)
    box = draw.textbbox((0, 0), text, font=fnt)
    width = box[2] - box[0] + 38
    draw.rounded_rectangle((x, y, x + width, y + 52), radius=16, fill=color + (225,))
    draw.text((x + 19, y + 9), text, font=fnt, fill=INK)
    return width


def wrap(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        if sum(len(item) for item in current) + len(current) + len(word) > limit:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def compose(size: tuple[int, int], social: bool = False) -> Image.Image:
    width, height = size
    img = gradient(size).convert("RGBA")
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.ellipse((width * 0.50, -height * 0.15, width * 1.10, height * 0.62), fill=CYAN + (52,))
    gd.ellipse((-width * 0.16, height * 0.55, width * 0.45, height * 1.16), fill=GOLD + (38,))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(34)))

    draw = ImageDraw.Draw(img, "RGBA")
    draw_grid(draw, width, height)
    draw_mcp_nodes(draw, width, height)

    margin = int(width * 0.07)
    top = int(height * 0.16)
    title_font = font(78 if not social else 64, bold=True)
    text_font = font(34 if not social else 29)
    footer_font = font(28 if not social else 24, bold=True)

    draw.rounded_rectangle(
        (margin - 34, top - 36, int(width * 0.58), int(height * 0.74)),
        radius=28,
        fill=PANEL + (188,),
        outline=(255, 255, 255, 34),
        width=2,
    )

    x = margin
    x += tag(draw, x, top, "ABLETON", GREEN) + 14
    x += tag(draw, x, top, "MCP", CYAN) + 14
    tag(draw, x, top, "STDIO", GOLD)

    title_y = top + 90
    draw.text((margin, title_y), "Ableton MCP", font=title_font, fill=WHITE)
    draw.text((margin, title_y + int(title_font.size * 1.05)), "Bridge", font=title_font, fill=WHITE)

    body = "Local Ableton Live status, paths, and launch instructions through a minimal MCP server."
    y = title_y + int(title_font.size * 2.25)
    for line in wrap(body, 40 if not social else 36):
        draw.text((margin + 3, y), line, font=text_font, fill=MUTED)
        y += int(text_font.size * 1.42)

    draw_wave(draw, (margin, int(height * 0.72), int(width * 0.54), int(height * 0.84)))
    draw.text((margin, height - 74), "integrations/ableton", font=footer_font, fill=WHITE)
    return img.convert("RGB")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    compose((1600, 900)).save(OUT / "repo-hero.png", quality=95)
    compose((1200, 630), social=True).save(OUT / "github-social-preview.png", quality=95)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

