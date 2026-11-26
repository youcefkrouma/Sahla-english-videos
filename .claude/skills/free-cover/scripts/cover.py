#!/usr/bin/env python3
"""Free 1080x1920 cover / thumbnail in the Sahla English style (Pillow only).

  cover.py --ar "تقولها في الليل؟" --en "Good afternoon?" --num 3 \
           --image refs/fahimo-ref.png --theme night -o covers/03-free.png

Arabic is shaped and ordered correctly (Pillow + libraqm). Titles and the
character stay inside the 3:4 grid crop that TikTok and Instagram show on
the profile page (y 240..1680), so nothing important is cut.

Themes: night, day, sunny, sky, grass, candy, purple
Decorations: --deco stars,sun,moon,hearts,dots  (any mix, or none)
"""
import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
GRID_TOP, GRID_BOTTOM = 240, 1680          # 3:4 profile-grid crop
REPO = Path(__file__).resolve().parents[4]
FONTS = REPO / "assets/fonts"

THEMES = {  # ray colour A, ray colour B, centre glow, title ink, outline
    "night": ("#1b2a6b", "#2d3a5c", "#f4c95d", "#ffffff", "#0d1433"),
    "day": ("#2f8fd8", "#4aa8ea", "#fff3b0", "#ffffff", "#0b3a66"),
    "sunny": ("#ff9f1c", "#ffbf47", "#fff7d6", "#ffffff", "#7a3300"),
    "sky": ("#5ec8f2", "#86dbfa", "#ffffff", "#ffffff", "#0b4f6c"),
    "grass": ("#3aa655", "#59c272", "#f7ffd6", "#ffffff", "#0f4020"),
    "candy": ("#ff6fa5", "#ff93bd", "#fff0f6", "#ffffff", "#6b0f37"),
    "purple": ("#5b3cc4", "#7653de", "#ffe27a", "#ffffff", "#1f0f5c"),
}
EN_INK = "#ffcf33"


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size, layout_engine=ImageFont.Layout.RAQM)
    if weight:
        try:
            f.set_variation_by_name(weight)
        except (OSError, ValueError):
            pass
    return f


def hex2rgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def rays(img, c1, c2, n=28, cx=W // 2, cy=1100):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=c1)
    r = 3000
    for i in range(0, n, 2):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=c2)


def glow(img, colour, cx=W // 2, cy=1100, radius=520, strength=150):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                                  fill=hex2rgb(colour, strength))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius // 2)))


def vignette(img):
    v = Image.new("L", img.size, 0)
    ImageDraw.Draw(v).ellipse([-300, -200, W + 300, H + 200], fill=255)
    v = ImageChops.invert(v.filter(ImageFilter.GaussianBlur(220)))
    dark = Image.new("RGBA", img.size, (0, 0, 20, 0))
    dark.putalpha(v.point(lambda p: int(p * 0.55)))
    img.alpha_composite(dark)


def cut_out(path, tol=28):
    """Character with transparent background. Keeps alpha if present,
    otherwise removes a plain light background connected to the borders."""
    im = Image.open(path).convert("RGBA")
    if im.getextrema()[3][0] < 250:
        return im
    rgb = im.convert("RGB")
    w, h = rgb.size
    mask = Image.new("L", (w, h), 0)
    seeds = [(x, 0) for x in range(0, w, 8)] + [(x, h - 1) for x in range(0, w, 8)] + \
            [(0, y) for y in range(0, h, 8)] + [(w - 1, y) for y in range(0, h, 8)]
    work = rgb.copy()
    key = (255, 0, 255)
    for s in seeds:
        if work.getpixel(s) != key and min(work.getpixel(s)) > 200:
            ImageDraw.floodfill(work, s, key, thresh=tol)
    r, g, b = work.split()
    bg = ImageChops.multiply(ImageChops.multiply(r.point(lambda p: 255 if p == 255 else 0),
                                                 g.point(lambda p: 255 if p == 0 else 0)),
                             b.point(lambda p: 255 if p == 255 else 0))
    alpha = ImageChops.invert(bg).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    im.putalpha(alpha)
    return im.crop(im.getbbox())


def text_block(img, text, fnt, ink, outline, cy, max_w=980, stroke=14, shadow=True):
    """Draw centred text with outline and soft shadow; shrink to fit max_w."""
    size = fnt.size
    while True:
        box = ImageDraw.Draw(img).textbbox((0, 0), text, font=fnt, stroke_width=stroke, anchor="mm")
        if box[2] - box[0] <= max_w or size <= 40:
            break
        size -= 4
        fnt = fnt.font_variant(size=size)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((W // 2 + 6, cy + 12), text, font=fnt, fill=(0, 0, 0, 150),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 150), anchor="mm")
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(img).text((W // 2, cy), text, font=fnt, fill=ink, stroke_width=stroke,
                             stroke_fill=outline, anchor="mm")
    return box[3] - box[1]


def pill(img, xy, text, fnt, fill, ink, pad=(34, 14)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    l, t, r, b = d.textbbox((0, 0), text, font=fnt, anchor="lt")
    x, y = xy
    w, h = r - l + 2 * pad[0], b - t + 2 * pad[1]
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=fill)
    img.alpha_composite(layer)
    ImageDraw.Draw(img).text((x + pad[0] - l, y + pad[1] - t), text, font=fnt, fill=ink, anchor="lt")
    return w, h


def star(d, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def heart(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r * 0.8, cx, cy + r * 0.2], fill=fill)
    d.ellipse([cx, cy - r * 0.8, cx + r, cy + r * 0.2], fill=fill)
    d.polygon([(cx - r * 0.97, cy - r * 0.15), (cx + r * 0.97, cy - r * 0.15), (cx, cy + r)], fill=fill)


def decorate(img, kinds, seed):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    if "sun" in kinds:
        cx, cy, r = 165, 830, 62
        for k in range(12):
            a = k * math.pi / 6
            d.line([(cx + 90 * math.cos(a), cy + 90 * math.sin(a)), (cx + 118 * math.cos(a), cy + 118 * math.sin(a))],
                   fill="#ffcf33", width=12)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffcf33")
    if "moon" in kinds:
        cx, cy, r = 905, 850, 72
        moon = Image.new("RGBA", img.size, (0, 0, 0, 0))
        md = ImageDraw.Draw(moon)
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#f6efcf")
        md.ellipse([cx - r + 34, cy - r - 18, cx + r + 34, cy + r - 18], fill=(0, 0, 0, 0))
        img.alpha_composite(moon)
    ring = [(a, rr) for a, rr in zip(range(0, 360, 30), [430, 470] * 6)]
    for a, rr in ring:
        x = W // 2 + rr * math.cos(math.radians(a)) * 0.95
        y = 1180 + rr * math.sin(math.radians(a)) * 1.05
        if not (GRID_TOP + 420 < y < GRID_BOTTOM - 40):
            continue
        if "stars" in kinds:
            star(d, x, y, rnd.choice([18, 24, 30]), rnd.choice(["#ffcf33", "#ffffff"]))
        if "hearts" in kinds:
            heart(d, x + 30, y - 20, 18, "#ff5c8a")
        if "dots" in kinds:
            d.ellipse([x - 7, y + 30, x + 7, y + 44], fill="#ffffff")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ar", default="", help="Arabic title (top line)")
    ap.add_argument("--en", default="", help="English phrase (yellow line)")
    ap.add_argument("--num", help="episode number shown in the yellow pill")
    ap.add_argument("--brand", default="Sahla English")
    ap.add_argument("--image", default=str(REPO / "refs/fahimo-ref.png"), help="character PNG")
    ap.add_argument("--bg-image", help="use a picture as background instead of rays")
    ap.add_argument("--theme", default="night", choices=sorted(THEMES))
    ap.add_argument("--deco", default="stars", help="stars,sun,moon,hearts,dots or none")
    ap.add_argument("--char-height", type=int, default=1000, help="character height in px")
    ap.add_argument("--guides", action="store_true", help="draw the grid-crop lines (for checking)")
    ap.add_argument("-o", "--output", default="cover.png")
    a = ap.parse_args()

    c1, c2, glow_c, ink, outline = THEMES[a.theme]
    img = Image.new("RGBA", (W, H))
    if a.bg_image:
        bg = Image.open(a.bg_image).convert("RGBA")
        s = max(W / bg.width, H / bg.height)
        bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
        img.alpha_composite(bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                                     (bg.width - W) // 2 + W, (bg.height - H) // 2 + H)))
    else:
        rays(img, c1, c2)
    glow(img, glow_c)
    vignette(img)
    decorate(img, set(a.deco.split(",")) - {"none"}, seed=a.num or 1)

    # titles first on their own layer, to know where the character may start
    txt = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pf = font("BalooBhaijaan2[wght].ttf", 46, "ExtraBold")
    pw, ph = ImageDraw.Draw(txt).textbbox((0, 0), a.brand, font=pf)[2:]
    nw = (ImageDraw.Draw(txt).textbbox((0, 0), f"#{a.num}", font=pf)[2] + 68 + 24) if a.num else 0
    x0 = (W - (pw + 68 + nw)) // 2
    pill(txt, (x0, GRID_TOP + 30), a.brand, pf, (255, 255, 255, 70), "#ffffff")
    if a.num:
        pill(txt, (x0 + pw + 68 + 24, GRID_TOP + 30), f"#{a.num}", pf, "#ffcf33", "#1b2a6b")
    cy = GRID_TOP + 200
    if a.ar:
        hgt = text_block(txt, a.ar, font("Lalezar-Regular.ttf", 150), ink, outline, cy)
        cy += hgt // 2 + 95
    if a.en:
        text_block(txt, a.en, font("BalooBhaijaan2[wght].ttf", 140, "ExtraBold"), EN_INK, outline, cy)
    title_bottom = (txt.getbbox() or (0, 0, 0, GRID_TOP))[3]

    # character, bottom-anchored inside the grid crop, with a soft floor shadow
    ch = cut_out(a.image)
    room = GRID_BOTTOM - 20 - (title_bottom + 10)
    s = min(a.char_height, room) / ch.height
    ch = ch.resize((round(ch.width * s), round(ch.height * s)), Image.LANCZOS)
    if ch.width > 1000:
        ch = ch.resize((1000, round(ch.height * 1000 / ch.width)), Image.LANCZOS)
    x, y = (W - ch.width) // 2, GRID_BOTTOM - 20 - ch.height
    floor = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(floor).ellipse([W // 2 - 300, GRID_BOTTOM - 70, W // 2 + 300, GRID_BOTTOM + 10], fill=(0, 0, 0, 110))
    img.alpha_composite(floor.filter(ImageFilter.GaussianBlur(25)))
    img.alpha_composite(ch, (x, y))

    img.alpha_composite(txt)

    if a.guides:
        d = ImageDraw.Draw(img)
        for gy in (GRID_TOP, GRID_BOTTOM):
            d.line([(0, gy), (W, gy)], fill="#ff0000", width=4)
    img.convert("RGB").save(a.output, optimize=True)
    print(f"Done: {a.output} ({W}x{H})")


if __name__ == "__main__":
    main()
