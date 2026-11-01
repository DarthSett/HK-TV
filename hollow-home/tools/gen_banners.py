"""Themed 640x360 app banners (dock tiles, grid tiles, app icon) -> dist/out/banner-<key>.png

Pale, thin-lined 'old engraving' look: dark gradient panel, double hairline frame with small
ornaments, pale logo with a soft glow, Cinzel caps for the label. Logos are Simple Icons (CC0).
Needs: pillow numpy cairosvg.   usage: python3 -I tools/gen_banners.py <repo_root>
"""
import io, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
try:
    import cairosvg
except OSError:                     # Windows without the Cairo DLL: render the logos with PyMuPDF instead
    cairosvg = None
    import pymupdf

B = sys.argv[1]
F = B + '/fonts/'
os.makedirs(B + '/dist/out', exist_ok=True)
PALE = (214, 232, 238)
LOGO = (236, 244, 246)
BW, BH = 640, 360


def svg_white(path, h):
    s = open(path).read().replace('<path ', '<path fill="#ffffff" ')
    if cairosvg:
        png = cairosvg.svg2png(bytestring=s.encode(), output_height=h)
    else:
        page = pymupdf.open(stream=s.encode(), filetype='svg')[0]; z = h / page.rect.height
        png = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=True).tobytes('png')
    return Image.open(io.BytesIO(png)).convert('RGBA')


def tint(im, rgb):
    a = im.split()[3]
    out = Image.new('RGBA', im.size, rgb + (0,)); out.putalpha(a); return out


def diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def panel():
    g = np.linspace(0, 1, BH)[:, None, None]
    top, bot = np.array([16, 25, 29]), np.array([4, 7, 9])
    arr = np.broadcast_to(top[None, None] * (1 - g) + bot[None, None] * g, (BH, BW, 3)).copy()
    yy, xx = np.mgrid[0:BH, 0:BW]
    arr *= (1 - .35 * (((xx - BW / 2) / (BW / 2)) ** 2 + ((yy - BH / 2) / (BH / 2)) ** 2) / 2)[..., None]   # soft vignette
    cut = 16
    poly = [(cut, 0), (BW - cut, 0), (BW, cut), (BW, BH - cut), (BW - cut, BH), (cut, BH), (0, BH - cut), (0, cut)]
    msk = Image.new('L', (BW, BH), 0); ImageDraw.Draw(msk).polygon(poly, fill=255)
    im = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    im.paste(Image.fromarray(arr.astype(np.uint8)).convert('RGBA'), (0, 0), msk)
    d = ImageDraw.Draw(im)
    d.line(poly + [poly[0]], fill=PALE + (190,), width=2)                       # outer frame
    i = 11
    inner = [(cut + i, i), (BW - cut - i, i), (BW - i, cut + i), (BW - i, BH - cut - i), (BW - cut - i, BH - i), (cut + i, BH - i), (i, BH - cut - i), (i, cut + i)]
    d.line(inner + [inner[0]], fill=PALE + (70,), width=1)                      # inner hairline
    for cx, cy in [(BW // 2, 0), (BW // 2, BH - 1)]:                            # centre ornaments on the frame
        diamond(d, cx, cy, 7, PALE + (230,)); diamond(d, cx, cy, 3, (6, 10, 12, 255))
    for x, y in [(cut + i, i), (BW - cut - i, i), (cut + i, BH - i), (BW - cut - i, BH - i)]:
        diamond(d, x, y, 3, PALE + (160,))
    return im


def glowpaste(im, logo, xy):
    pad = 40
    big = Image.new('RGBA', (logo.width + 2 * pad, logo.height + 2 * pad), (0, 0, 0, 0))
    big.paste(logo, (pad, pad)); logo = big; xy = (xy[0] - pad, xy[1] - pad)
    g = tint(logo, (170, 205, 218)).filter(ImageFilter.GaussianBlur(9))
    im.alpha_composite(g, xy)
    im.alpha_composite(tint(logo, LOGO), xy)


label = ImageFont.truetype(F + 'Cinzel.ttf', 38); label.set_variation_by_name('Bold')
APPS = {  # key: (svg in logos/ or None, label, text logo when there is no svg)
    'home': (None, 'HOME', 'HOME'),
    'netflix': ('netflix', 'NETFLIX', None), 'primevideo': ('primevideo', 'PRIME VIDEO', None),
    'hotstar': (None, 'HOTSTAR', 'hotstar'), 'youtube': ('youtube', 'YOUTUBE', None), 'twitch': ('twitch', 'TWITCH', None),
    'youtubemusic': ('youtubemusic', 'YT MUSIC', None), 'plex': ('plex', 'PLEX', None), 'kodi': ('kodi', 'KODI', None),
    'appletv': ('appletv', 'APPLE TV', None), 'max': (None, 'MAX', 'max'), 'vlc': ('vlc', 'VLC', None),
    'playstore': ('googleplay', 'PLAY STORE', None), 'downloader': ('arrow', 'DOWNLOADER', None),
    'livetv': ('tv', 'LIVE TV', None), 'inputs': ('arrow', 'INPUTS', None),
    'apps': ('grid', 'APPS', None), 'ponte': ('cam', 'BRIDGE', None), 'settings': ('gear', 'SETTINGS', None),
}
for key, (svg, name, txt) in APPS.items():
    im = panel()
    if svg:
        logo = svg_white(f'{B}/logos/{svg}.svg', 600)
        logo = logo.crop(logo.getbbox())
        k = min(340 / logo.width, 118 / logo.height)
        logo = logo.resize((round(logo.width * k), round(logo.height * k)), Image.LANCZOS)
    else:
        ft = ImageFont.truetype(F + 'Cinzel.ttf', 104 if len(txt) > 2 else 150); ft.set_variation_by_name('Bold')
        bb = ft.getbbox(txt); logo = Image.new('RGBA', (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(logo).text((10 - bb[0], 10 - bb[1]), txt, font=ft, fill='white')
    x = (BW - logo.width) // 2; y = 136 - logo.height // 2
    glowpaste(im, logo, (x, y))
    d = ImageDraw.Draw(im)
    ly = BH - 100                                                                 # divider with a small diamond above the label
    d.line([(BW // 2 - 90, ly), (BW // 2 - 12, ly)], fill=PALE + (110,), width=1)
    d.line([(BW // 2 + 12, ly), (BW // 2 + 90, ly)], fill=PALE + (110,), width=1)
    diamond(d, BW // 2, ly, 4, PALE + (200,))
    tw = d.textlength(name, font=label)
    d.text(((BW - tw) / 2, BH - 86), name, font=label, fill=PALE + (235,))
    im.save(f'{B}/dist/out/banner-{key}.png')
print('ok', len(APPS), 'banners')
