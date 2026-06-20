#!/usr/bin/env python3
"""
Antagonist portrait pipeline — Mistbound Gothic, bestiary build.

Every output pixel derives from a committed Eldritch source illustration
under _sources/ (downloaded from the Drive Bestiary/ folder, or the local
skull.png plate). The transforms are: rectangular portrait crop -> light
desaturate -> LIGHT tritone tint toward the Mistbound palette -> radial
vignette -> gold frame. NO external/stock/AI art is introduced; only the
source pixels are remapped.

Design correction from review:
  * The combat panel (CombatEncounterPanel) frames RECTANGULARLY (3:4),
    so we crop to a 3:4 portrait window rather than a tight circle.
  * The tint is dialed LIGHT (low blend toward the duotone) so busy
    bestiary linework stays legible instead of muddying.

Run from frontend/public/art/antagonists/:
    python3 _pipeline.py
"""
import os
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "_sources")

# Mistbound Gothic palette (from frontend/src/App.css)
VOID   = (10, 8, 7)        # --void  : deepest shadow anchor
SHADOW = (20, 24, 23)      # near-void with a cold cast for duotone floor
MIST   = (163, 181, 168)   # --mist  : cold verdigris, the living highlight
HILITE = (214, 226, 216)   # brightened verdigris highlight
GOLD   = (212, 175, 55)    # --accent-gold : frame only
BLOOD  = (139, 0, 0)       # --accent-blood

OUT_W = 512          # output width  (px)
OUT_H = 683          # output height (px) -> 3:4 portrait, matches cep-frame
FRAME = 20           # gold frame thickness (px)
INNER_RADIUS = 12    # rounded inner window corner radius

# How strongly to pull the source toward the tritone. LIGHT keeps the
# original art readable; review flagged the previous heavy tritone as muddy.
TINT_STRENGTH = 0.45   # 0 = original colour, 1 = full tritone
VOID_BLEND = 0.05      # whisper toward void so bone-prose stays brightest

# Each antagonist: source file + the portrait crop box as fractions of the
# source (left, top, right, bottom), chosen to frame the face/upper body in
# a 3:4 window. `blood` lifts the duotone midtones toward menace. `center`
# is the ImageOps.fit vertical centering bias (lower = favour the top/face).
PORTRAITS = {
    "wight": {
        "src": "wight.jpg",
        "crop": (0.10, 0.04, 0.92, 0.78),
        "blood": 0.06, "center": 0.30,
    },
    "revenant": {
        "src": "revenant.jpg",
        "crop": (0.06, 0.00, 0.96, 0.80),
        "blood": 0.10, "center": 0.18,
    },
    "netherphage": {
        "src": "netherphage.jpg",
        "crop": (0.04, 0.00, 0.98, 0.82),
        "blood": 0.14, "center": 0.12,
    },
    "nethermancer": {
        "src": "nethermancer.jpg",
        "crop": (0.10, 0.04, 0.92, 0.60),
        "blood": 0.12, "center": 0.24,
    },
    "necromancer": {
        "src": "necromancer.jpg",
        "crop": (0.14, 0.03, 0.90, 0.66),
        "blood": 0.06, "center": 0.26,
    },
    "werewolf": {
        "src": "werewolf.jpg",
        "crop": (0.06, 0.04, 0.96, 0.78),
        "blood": 0.10, "center": 0.30,
    },
    # risen_dead / unhallowed_spawn share the local skull plate (Bones_.png
    # is >10MB, over the Drive MCP download limit — documented substitution).
    "risen_dead": {
        "src": "skull.png",
        "crop": (0.06, 0.04, 0.94, 0.92),
        "blood": 0.04, "center": 0.45,
    },
    "unhallowed_spawn": {
        "src": "skull.png",
        "crop": (0.10, 0.02, 0.90, 0.86),
        "blood": 0.16, "center": 0.42,
    },
}


def duotone(gray, shadow, light, mid=MIST, blood_mix=0.0):
    """Map an L-mode image onto a shadow->mid->light gradient (a tritone)."""
    if blood_mix:
        mid = tuple(round(m + (b - m) * blood_mix) for m, b in zip(mid, BLOOD))
    lut_r, lut_g, lut_b = [], [], []
    for i in range(256):
        t = i / 255.0
        if t < 0.5:
            u = t / 0.5
            r = shadow[0] + (mid[0] - shadow[0]) * u
            g = shadow[1] + (mid[1] - shadow[1]) * u
            b = shadow[2] + (mid[2] - shadow[2]) * u
        else:
            u = (t - 0.5) / 0.5
            r = mid[0] + (light[0] - mid[0]) * u
            g = mid[1] + (light[1] - mid[1]) * u
            b = mid[2] + (light[2] - mid[2]) * u
        lut_r.append(round(r)); lut_g.append(round(g)); lut_b.append(round(b))
    return Image.merge("RGB", [gray.point(lut_r), gray.point(lut_g), gray.point(lut_b)])


def radial_vignette(size, strength=0.7):
    """A soft dark radial mask: bright centre, void edges."""
    w, h = size
    big = max(w, h) * 2
    grad = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(grad)
    cx, cy = big // 2, big // 2
    steps = 64
    for i in range(steps, 0, -1):
        r = int((big / 2) * (i / steps))
        v = int(255 * (1 - (i / steps) ** 2 * strength))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    return grad.resize((w, h), Image.LANCZOS)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def make_portrait(key, cfg):
    src_path = os.path.join(SRC, cfg["src"])
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    l, t, r, b = cfg["crop"]
    box = (int(l * w), int(t * h), int(r * w), int(b * h))
    crop = im.crop(box)

    inner_w, inner_h = OUT_W - 2 * FRAME, OUT_H - 2 * FRAME
    crop = ImageOps.fit(crop, (inner_w, inner_h), Image.LANCZOS,
                        centering=(0.5, cfg.get("center", 0.3)))

    # LIGHT tone: blend the tritone over a contrast-tweaked colour base,
    # so the original art reads through but is unified into the palette.
    base = ImageOps.autocontrast(crop, cutoff=1)
    gray = ImageOps.autocontrast(ImageOps.grayscale(crop), cutoff=1)
    toned = duotone(gray, SHADOW, HILITE, mid=MIST, blood_mix=cfg["blood"])
    toned = Image.blend(base, toned, TINT_STRENGTH)

    toned = Image.blend(toned, Image.new("RGB", toned.size, VOID), VOID_BLEND)

    # radial vignette pulls the edges into void, focusing the subject
    vig = radial_vignette(toned.size, strength=0.6)
    dark = Image.new("RGB", toned.size, SHADOW)
    toned = Image.composite(toned, dark, vig)

    # faint verdigris bloom on the brightest areas (one ambient glow)
    bloom = toned.filter(ImageFilter.GaussianBlur(7))
    toned = ImageChops.screen(toned, ImageChops.multiply(
        bloom, Image.new("RGB", toned.size, (40, 48, 44))))

    inner_mask = rounded_mask(toned.size, INNER_RADIUS)

    canvas = Image.new("RGBA", (OUT_W, OUT_H), (*VOID, 255))
    fd = ImageDraw.Draw(canvas)
    fd.rounded_rectangle([1, 1, OUT_W - 2, OUT_H - 2], radius=INNER_RADIUS + FRAME,
                         outline=(*GOLD, 255), width=3)
    fd.rounded_rectangle([FRAME - 4, FRAME - 4, OUT_W - FRAME + 3, OUT_H - FRAME + 3],
                         radius=INNER_RADIUS + 4, outline=(*GOLD, 180), width=2)

    art = Image.new("RGBA", toned.size, (0, 0, 0, 0))
    art.paste(toned, (0, 0), inner_mask)
    canvas.alpha_composite(art, (FRAME, FRAME))

    out_path = os.path.join(HERE, f"{key}-portrait.png")
    canvas.save(out_path)
    print(f"wrote {out_path}  <- {cfg['src']} crop={cfg['crop']}")


if __name__ == "__main__":
    for key, cfg in PORTRAITS.items():
        make_portrait(key, cfg)
