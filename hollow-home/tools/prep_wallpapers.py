"""Prepare wallpaper stills: cover-fit to 1920x1080, shift the picture up by `shift` px
and fill the strip that opens at the bottom with a blurred, darkened mirror of the
image's own bottom edge (the bottoms are dark silhouettes, so it reads as more ground).

usage: python3 -I prep.py <originals_dir> <out_dir>
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080
src_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

# name: (source file, crop-centre x as fraction of the scaled width, upward shift in px)
JOBS = {
    'memorial-rain':  ('memorial-rain.avif',  0.50,  40),
    'butterflies':    ('butterflies.avif',    0.50,   0),
    'flowers':        ('flowers.avif',        0.46,  90),
    'chamber':        ('chamber.jpg',         0.50, 110),
    'pixel':          ('pixel.jpg',           0.50, 120),
    'green-clearing': ('green-clearing-clean.png', 0.50, 120),   # game interface painted out (tools/clean_hud.py), lifted above the dock
}


def cover(im, cx):
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0 = round(min(max(cx * im.width - W / 2, 0), im.width - W))
    y0 = (im.height - H) // 2
    return im.crop((x0, y0, x0 + W, y0 + H))


def shift_up(im, d):
    if d <= 0:
        return im
    a = np.asarray(im).astype(np.float32)
    top = a[d:]                                     # picture moved up, top d rows cropped away
    strip = a[H - d:][::-1]                         # mirror of the bottom d rows
    strip = np.asarray(Image.fromarray(strip.astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(np.float32)
    fade = np.linspace(0.85, 0.25, d)[:, None, None]   # darker the further down
    out = np.concatenate([top, strip * fade], axis=0)
    # soften the seam
    s0 = H - d
    seam = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    band = seam.crop((0, s0 - 10, W, s0 + 10)).filter(ImageFilter.GaussianBlur(3))
    seam.paste(band, (0, s0 - 10))
    return seam


try:
    import pillow_avif  # noqa: F401  (only needed if Pillow lacks native AVIF)
except Exception:
    pass

for name, (fn, cx, d) in JOBS.items():
    im = Image.open(os.path.join(src_dir, fn)).convert('RGB')
    out = shift_up(cover(im, cx), d)
    p = os.path.join(out_dir, name + '.jpg')
    out.save(p, quality=90, optimize=True, progressive=True, subsampling=0)
    print(f'{name:15s} src={im.size} shift={d:3d} -> {out.size} {os.path.getsize(p)//1024} KB')
