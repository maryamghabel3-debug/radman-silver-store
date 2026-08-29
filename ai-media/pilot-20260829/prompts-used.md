# Prompts Used — RADMAN SILVER 925 Media Cleaning Pilot (2026-08-29)

## 1. Ecommerce watermark cleaning

**No generative prompt was used for the mandatory cleaned ecommerce images.**
Cleaning was performed deterministically in-process (OpenCV) so that pixels outside
the repair mask stay bit-identical — a hard requirement that diffusion-style
inpainting cannot guarantee. The canonical prompt pair below is recorded for the
production phase, where a generative pass may be A/B-tested against the
deterministic pipeline on non-overlap cases only.

### Cleaning prompt (canonical, from project brief)
> Remove only the visible old watermark, logo or unrelated text overlay, especially
> «نقره مشهد», “noghrehmashhad.ir”, old seller branding or old promotional text.
> Reconstruct only the small covered background area. Preserve the exact real ring,
> gemstone color, gemstone pattern, silver band, authentic engravings, inscriptions,
> lighting, shadows, reflections, composition, dimensions and product identity.
> No new objects, no style change and no product regeneration.

### Negative prompt (canonical, from project brief)
> altered ring, changed gemstone, changed stone color, changed stone pattern,
> fake jewelry, invented engraving, removed authentic inscription, modified silver
> band, excessive shine, smooth metal details, blur, new text, new logo, human hand,
> mannequin, background replacement, distorted product, CGI ring

### Deterministic pipeline actually used (scripts/clean_watermark.py, v3)
1. Vivid-gold core detection (HSV inRange H13–34, S≥80–100, V≥90–95) in bottom ROI
   (y ≥ 0.64·H); components filtered by vivid-stroke density ≥ 0.55
   (calibrated: logo strokes 0.57–0.95, ring reflections 0.13–0.53).
2. Grow bounding box +60 px around the core; accept pale-to-vivid gold
   (H10–40, S≥25, V≥70) inside the box → captures the pale ornamental frame.
3. Clamp mask to human-reviewed per-image windows (`scripts/mask-review.json`).
4. Inpaint with **OpenCV xphoto FSR_FAST** (patch-based, frequency domain);
   feathered 1.5 px boundary blend.
5. Numeric assertion: eroded non-mask region must be bit-identical to original.

## 2. Male-lifestyle social tests (generative, explicitly experimental)

Reference image supplied = cleaned product cutout (U²-Net alpha). Prompt template:

> Photorealistic premium jewelry lifestyle photograph: a men's 925 sterling silver
> ring worn naturally on the ring finger of an adult man's hand. The ring is EXACTLY
> the reference product: {stone + band description from the real photo} — do not
> change the gemstone color, shape, band engraving or proportions. Hand: masculine,
> natural skin texture, correct anatomy, relaxed pose. Setting: {dark suit cuff /
> premium leather}, moody premium studio lighting with subtle warm golden accent.
> No face, no text, no logo, no watermark, no other jewelry.

Per-product fidelity verdicts: product-211 PASS, product-184 PASS,
product-214 PASS on second attempt (first attempt simplified dendritic
inclusions → rejected per VIDEO/IMAGE fidelity rule and regenerated with
pixel-faithful pattern language).

## 3. Persian text overlay (deterministic — model never asked to draw text)

No prompt. Rendered with Pillow + Raqm (`direction='rtl'`), font **Vazirmatn Bold**
(OFL). Texts: «رادمان سیلور ۹۲۵» / «انگشتر نقره مردانه» / «اصالت نقره، جلوه سنگ» /
«مشاهده مجموعه». Placement restricted to bands verified content-free by pixel-diff
against the regenerated background; editable transparent layer + JSON placements
exported (`social/posts/product-211-overlay-meta.json`).

## 4. Video pilot

No generative video model was used (no authorized API available). The 5 s vertical
clip was rendered deterministically from the approved `luxury-dark` master:
affine push-in 1.000→1.045 (smoothstep), 10 px lateral parallax, Gaussian light-drift
overlay. Zero morphing/rotation risk by construction → product identity preserved.
