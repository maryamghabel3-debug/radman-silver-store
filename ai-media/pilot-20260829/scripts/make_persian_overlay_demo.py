#!/usr/bin/env python3
"""Persian overlay DEMO (deterministic graphics only — no image model).
Base: text-free master. Text drawn with Vazirmatn (RTL shaping via raqm),
placed only in rows verified empty (no overlap with ring / UI elements).
Layer positions are exported to JSON so the overlay stays editable.
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

POST = os.path.expanduser('~/pilot/experiments/product-211/instagram-post-4x5.jpg')
OUTD = os.path.expanduser('~/pilot/social/posts')
FONT = os.path.expanduser('~/.fonts/Vazirmatn-Bold.ttf')
GOLD = (201, 162, 91)
IVORY = (243, 238, 227)

BRAND = "رادمان سیلور ۹۲۵"
TITLE = "انگشتر نقره مردانه"
SUB = "اصالت نقره، جلوه سنگ"
CTA = "مشاهده مجموعه"

os.makedirs(OUTD, exist_ok=True)
master = Image.open(POST).convert('RGB')
W, H = master.size

# ---- find rows fully free of product/UI (diff vs regenerated background) ----
import sys
sys.path.insert(0, os.path.expanduser('~/pilot/scripts'))
from make_experiments import dark_bg
bg = np.array(dark_bg(W, H).convert('RGB'), int)
m = np.array(master, int)
diff = np.abs(m - bg).sum(axis=2)
busy = (diff > 12).sum(axis=1) > 6          # rows containing content
free_rows = ~busy
# group free bands
bands = []
start = None
for y in range(H):
    if free_rows[y] and start is None:
        start = y
    elif not free_rows[y] and start is not None:
        if y - start >= 90:
            bands.append((start, y))
        start = None
if start is not None and H - start >= 90:
    bands.append((start, H))
print("free bands:", bands)

# choose top band for brand+title, bottom band for subtitle+CTA
top = max(bands, key=lambda b: b[0] if b[1] < H * 0.5 else -1)
bottom = max(bands, key=lambda b: b[1] if b[0] > H * 0.5 else -1)

layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
placements = {}

f_brand = ImageFont.truetype(FONT, 34)
f_title = ImageFont.truetype(FONT, 58)
f_sub   = ImageFont.truetype(FONT, 34)
f_cta   = ImageFont.truetype(FONT, 30)

y0, y1 = top
cy = (y0 + y1) // 2
d.text((W//2, cy - 44), BRAND, font=f_brand, fill=GOLD, anchor='mm',
       direction='rtl', features=['rtla'])
d.text((W//2, cy + 26), TITLE, font=f_title, fill=IVORY, anchor='mm',
       direction='rtl', features=['rtla'])
placements.update(brand=BRAND, title=TITLE, top_band=[y0, y1])

y0, y1 = bottom
cy = (y0 + y1) // 2
d.text((W//2, cy - 26), SUB, font=f_sub, fill=IVORY, anchor='mm',
       direction='rtl', features=['rtla'])
# CTA pill
tw = d.textlength(CTA, font=f_cta, direction='rtl')
bw, bh = int(tw + 90), 58
bx, by = (W - bw)//2, cy + 8
d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=29, outline=GOLD, width=2)
d.text((W//2, by + bh//2 - 1), CTA, font=f_cta, fill=GOLD, anchor='mm',
       direction='rtl', features=['rtla'])
placements.update(subtitle=SUB, cta=CTA, cta_box=[bx, by, bx+bw, by+bh], bottom_band=[y0, y1])

# subtle backdrop behind top text for readability (no ring overlap: bands are content-free)
comp = master.convert('RGBA')
comp.alpha_composite(layer)
out = comp.convert('RGB')
out.save(os.path.join(OUTD, 'product-211-post-4x5-persian-overlay-demo.jpg'), quality=92)
layer.save(os.path.join(OUTD, 'product-211-post-4x5-text-layer.png'))   # editable transparent layer
meta = {
    "font": "Vazirmatn-Bold (OFL, rastikerdar/vazirmatn)",
    "shaping": "PIL raqm RTL (direction=rtl)",
    "canvas": f"{W}x{H}",
    "layers": placements,
    "note": "text-free master remains the canonical social master; this demo shows the optional overlay"
}
json.dump(meta, open(os.path.join(OUTD, 'product-211-overlay-meta.json'), 'w'),
          ensure_ascii=False, indent=2)
print("overlay demo + editable text layer saved")
