"""Paint out the game HUD (soul orb, 7 health masks, geo counter) from the top-left of a 1920x1080 frame.
The masks sit on top of a real pale antler, so the mask is built from the HUD's known layout
(three boxes), not from a global brightness threshold that would also eat the artwork.
usage: python3 -I clean_hud.py <in.jpg> <out.png> <debug_before_after.png>
"""
import sys
import numpy as np, cv2

src, out, dbg = sys.argv[1:4]
im = cv2.imread(src)                               # BGR
H, W = im.shape[:2]
assert (W, H) == (1920, 1080), (W, H)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
lum = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)


def ell(k):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


mask = np.zeros((H, W), np.uint8)


def box_thresh(x0, y0, x1, y1, lum_min, sat_max, grow):
    m = np.zeros((H, W), np.uint8)
    sel = (lum[y0:y1, x0:x1] > lum_min) & (hsv[y0:y1, x0:x1, 1] < sat_max)
    m[y0:y1, x0:x1] = sel.astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ell(7))
    return cv2.dilate(m, ell(grow))


# A: soul orb, its wisp and the two bubbles (background there is near black, so a low threshold also takes the glow)
mask |= box_thresh(60, 55, 345, 228, 55, 140, 21)
# B: seven health masks, evenly spaced; ellipses a little larger than a mask
for i in range(7):
    cx, cy = 288 + i * 58.2, 112
    cv2.ellipse(mask, (round(cx), cy), (27, 33), 0, 0, 360, 255, -1)
# C: geo icon and number
mask |= box_thresh(255, 155, 415, 224, 85, 120, 11)

res = cv2.inpaint(im, mask, 7, cv2.INPAINT_TELEA)
# inpainting leaves smooth patches; add matching grain inside the filled area so it does not look airbrushed
rng = np.random.default_rng(1)
noise = rng.normal(0, 5, res.shape).astype(np.float32)
soft = cv2.GaussianBlur(mask, (0, 0), 3).astype(np.float32)[..., None] / 255.0
res = np.clip(res.astype(np.float32) + noise * soft, 0, 255).astype(np.uint8)
# The last three masks sit on a pale antler with vertical dark bars; plain inpainting smears them.
# The background there is vertical, so copy the strip 68 px lower (HUD-free) and blend it in.
OFF = 68
for i in (4, 5, 6):
    cx, cy = round(288 + i * 58.2), 112
    m = np.zeros((H, W), np.uint8)
    cv2.ellipse(m, (cx, cy), (31, 37), 0, 0, 360, 255, -1)
    a = cv2.GaussianBlur(m, (0, 0), 4).astype(np.float32)[..., None] / 255.0
    shifted = np.roll(res, -OFF, axis=0)           # row y now holds the pixels of row y+OFF
    res = (res.astype(np.float32) * (1 - a) + shifted.astype(np.float32) * a).astype(np.uint8)
cv2.imwrite(out, res)

x0, y0, x1, y1 = 40, 40, 760, 240
pair = np.concatenate([im[y0:y1, x0:x1], res[y0:y1, x0:x1]], axis=0)
cv2.imwrite(dbg, cv2.resize(pair, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC))
print('masked px:', int((mask > 0).sum()))
