"""
Procedural placeholder images for the demo seeder.

Generates on-brand (teal/amber) abstract artwork instead of pulling from the
network, so `seed_demo` works offline and produces deterministic output.
"""
from __future__ import annotations

import io
import math

from PIL import Image, ImageDraw, ImageFilter


# Brand-adjacent palettes; index picks a deterministic look per item.
_PALETTES = [
    ((13, 148, 136), (15, 118, 110)),    # teal 600 -> 700
    ((20, 184, 166), (13, 148, 136)),    # teal 500 -> 600
    ((45, 212, 191), (14, 116, 144)),    # teal 400 -> cyan 700
    ((245, 158, 11), (217, 119, 6)),     # amber 500 -> 600
    ((56, 189, 248), (13, 148, 136)),    # sky 400 -> teal 600
    ((129, 140, 248), (13, 148, 136)),   # indigo 400 -> teal 600
    ((16, 185, 129), (5, 150, 105)),     # emerald 500 -> 600
    ((251, 191, 36), (13, 148, 136)),    # amber 400 -> teal 600
]


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient(size, top, bottom):
    w, h = size
    base = Image.new('RGB', (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = (_lerp(top[0], bottom[0], t),
                    _lerp(top[1], bottom[1], t),
                    _lerp(top[2], bottom[2], t))
    return base.resize((w, h), Image.BILINEAR)


def _blobs(img, seed, count=4):
    """Soft translucent circles — mimics the design system's blur blobs."""
    w, h = img.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rnd = seed
    for i in range(count):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        cx = (rnd % w)
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        cy = (rnd % h)
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        r = int(min(w, h) * (0.18 + (rnd % 100) / 400))
        alpha = 26 + (i * 9)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=min(w, h) // 14))
    return Image.alpha_composite(img.convert('RGBA'), layer)


def _tooth(draw, cx, cy, scale, fill):
    """
    Molar silhouette: a wide rounded crown with a shallow cusp notch, then two
    short tapering roots. Built from primitives so no external asset is needed.
    """
    s = scale
    # Crown — two wide, shallow lobes fused by a body rectangle.
    draw.ellipse([cx - s, cy - s * 0.90, cx + s * 0.12, cy + s * 0.20], fill=fill)
    draw.ellipse([cx - s * 0.12, cy - s * 0.90, cx + s, cy + s * 0.20], fill=fill)
    draw.rectangle([cx - s * 0.96, cy - s * 0.40, cx + s * 0.96, cy + s * 0.30], fill=fill)
    # Roots — short, wide-based tapers with a V notch between them.
    draw.polygon([
        (cx - s * 0.94, cy + s * 0.22),
        (cx - s * 0.14, cy + s * 0.22),
        (cx - s * 0.46, cy + s * 0.94),
    ], fill=fill)
    draw.polygon([
        (cx + s * 0.14, cy + s * 0.22),
        (cx + s * 0.94, cy + s * 0.22),
        (cx + s * 0.46, cy + s * 0.94),
    ], fill=fill)


def _sparkle(draw, cx, cy, r, fill):
    """Four-point star — the classic 'clean/whitening' accent."""
    draw.polygon([
        (cx, cy - r), (cx + r * 0.18, cy - r * 0.18),
        (cx + r, cy), (cx + r * 0.18, cy + r * 0.18),
        (cx, cy + r), (cx - r * 0.18, cy + r * 0.18),
        (cx - r, cy), (cx - r * 0.18, cy - r * 0.18),
    ], fill=fill)


def make_image(seed: int, width: int = 1200, height: int = 800,
               motif: str = 'tooth') -> bytes:
    """
    Return JPEG bytes for a deterministic on-brand placeholder.

    `motif`:
      - 'tooth'   : centred molar silhouette (services, blog covers)
      - 'sparkle' : scattered stars (gallery tiles)
      - 'avatar'  : head-and-shoulders bust on a soft circle (profile photos)
    """
    top, bottom = _PALETTES[seed % len(_PALETTES)]
    img = _gradient((width, height), top, bottom)
    # Back to RGB: ImageDraw only alpha-blends `RGBA` fills when the *base*
    # image is RGB. Leaving it RGBA would paint every fill fully opaque.
    img = _blobs(img, seed + 7).convert('RGB')

    cx, cy = width // 2, height // 2
    solid = (255, 255, 255, 255)

    def stamp(paint, opacity):
        """
        Draw `paint(draw)` onto its own transparent layer, then composite the
        whole layer at `opacity`. Compositing once means overlapping primitives
        (crown lobes, roots) never double-blend into visible seams.
        """
        nonlocal img
        layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        paint(ImageDraw.Draw(layer))
        alpha = layer.getchannel('A').point(lambda a: int(a * opacity))
        layer.putalpha(alpha)
        img = Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')

    if motif == 'avatar':
        r = min(width, height) * 0.36
        head = r * 0.34
        head_cy = cy - r * 0.36
        body_w = r * 0.82
        body_top = cy + r * 0.16

        # Soft backing disc so the bust reads as a portrait crop.
        stamp(lambda d: d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=solid), 0.18)

        def bust(d):
            # Head sits fully above the shoulders, with a visible neck gap.
            d.ellipse([cx - head, head_cy - head, cx + head, head_cy + head], fill=solid)
            # Shoulders — top half of a wide ellipse starting below the head.
            d.pieslice(
                [cx - body_w, body_top, cx + body_w, body_top + body_w * 2.2],
                start=180, end=360, fill=solid,
            )
        stamp(bust, 0.92)

    elif motif == 'sparkle':
        base = int(min(width, height) * 0.16)
        stamp(lambda d: _tooth(d, cx, int(cy * 0.96), base * 1.5, solid), 0.22)
        specks = (
            (0.22, 0.24, 0.075, 0.92), (0.79, 0.20, 0.055, 0.66),
            (0.70, 0.76, 0.065, 0.92), (0.16, 0.74, 0.045, 0.66),
        )
        for fx, fy, fr, op in specks:
            stamp(
                lambda d, fx=fx, fy=fy, fr=fr: _sparkle(
                    d, int(width * fx), int(height * fy),
                    int(min(width, height) * fr), solid,
                ),
                op,
            )

    else:  # 'tooth'
        base = int(min(width, height) * 0.24)
        stamp(lambda d: _tooth(d, cx, int(cy * 0.94), base, solid), 0.92)
        stamp(
            lambda d: _sparkle(d, int(cx + base * 1.5), int(cy - base * 0.85),
                               int(base * 0.30), solid),
            0.78,
        )
        stamp(
            lambda d: _sparkle(d, int(cx - base * 1.6), int(cy + base * 0.35),
                               int(base * 0.20), solid),
            0.58,
        )

    # Subtle vignette so white cards don't blend into the artwork.
    vignette = Image.new('L', (width, height), 0)
    ImageDraw.Draw(vignette).ellipse(
        [-width * 0.15, -height * 0.15, width * 1.15, height * 1.15], fill=255
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=min(width, height) // 8))
    dark = Image.new('RGB', (width, height), (8, 47, 45))
    img = Image.composite(img.convert('RGB'), dark, vignette)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=86, optimize=True)
    return buf.getvalue()
