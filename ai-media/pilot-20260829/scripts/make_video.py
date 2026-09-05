#!/usr/bin/env python3
"""Video pilot: 5s vertical 1080x1920 MP4 from an approved cleaned master.
Slow cinematic push-in (~4.5%) + very subtle horizontal parallax + gentle
studio-light drift via a moving soft highlight overlay. Deterministic
(plain affine/lighting math, no generative video) -> zero morphing risk.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 5.0
N = int(FPS * DUR)
SRC = os.path.expanduser('~/pilot/experiments/product-211/luxury-dark.jpg')
OUT = os.path.expanduser('~/pilot/video/pilot-pushin-1080x1920.mp4')

base = Image.open(SRC).convert('RGB')

def frame(i):
    t = i / (N - 1)
    # push-in: 1.000 -> 1.045 ; slight ease (smoothstep)
    e = t * t * (3 - 2 * t)
    zoom = 1.0 + 0.045 * e
    dx = 10 * e  # subtle parallax drift, px at output scale
    ow, oh = int(W * zoom), int(H * zoom)
    x0 = (ow - W) / 2 + dx
    y0 = (oh - H) / 2
    f = base.resize((ow, oh), Image.LANCZOS).crop((int(x0), int(y0), int(x0) + W, int(y0) + H))
    # gentle studio light movement: soft warm highlight drifting slowly
    hl = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(hl)
    cx = int(W * (0.42 + 0.10 * np.sin(2 * np.pi * t)))
    cy = int(H * 0.34)
    r = int(H * 0.45)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=26)
    hl = hl.filter(ImageFilter.GaussianBlur(180))
    warm = Image.new('RGB', (W, H), (255, 214, 150))
    f = Image.composite(Image.blend(f, warm, 0.05), f, hl)
    return f

import imageio
os.makedirs(os.path.dirname(OUT), exist_ok=True)
w = imageio.get_writer(OUT, fps=FPS, codec='libx264', quality=8,
                       macro_block_size=None, ffmpeg_params=['-pix_fmt', 'yuv420p', '-profile:v', 'high'])
for i in range(N):
    w.append_data(np.array(frame(i)))
w.close()
print("video written:", OUT)
