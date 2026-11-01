"""Contact sheet with the launcher's dock and clock zones drawn over each wallpaper.
usage: python3 -I sheet.py <wallpapers_dir> <out_png>
"""
import sys, os
from PIL import Image, ImageDraw

src, out = sys.argv[1], sys.argv[2]
names = ['memorial-rain', 'butterflies', 'flowers', 'chamber', 'pixel', 'green-clearing']
S = 0.5                                   # half scale: 960x540 per tile
tw, th = int(1920 * S), int(1080 * S)
sheet = Image.new('RGB', (tw * 2 + 30, (th + 40) * 3 + 10), (20, 20, 20))
d0 = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(src, n + '.jpg')).convert('RGB').resize((tw, th), Image.LANCZOS)
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # dock 96..1824 x 800..967, clock ~ right 96, top 58, 420x170, text line (if used) 96..1396 x 196..264
    for (x0, y0, x1, y1), col in [((96, 800, 1824, 967), (255, 60, 60, 70)),
                                  ((1404, 58, 1824, 228), (60, 160, 255, 70)),
                                  ((96, 196, 1396, 264), (255, 220, 60, 40))]:
        d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=col, outline=col[:3] + (200,))
    im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    x, y = 10 + (i % 2) * (tw + 10), 10 + (i // 2) * (th + 40)
    sheet.paste(im, (x, y)); d0.text((x, y + th + 6), n, fill=(230, 230, 230))
sheet.save(out); print(sheet.size)
