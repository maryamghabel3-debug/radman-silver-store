# Prompts Used — Media System v4 (P137, 2026-08-31)

## Image A — faithful main ecommerce photo (NO generative prompt)
Built deterministically; the ring pixels are 100% real (attachment 141).
Pipeline: u2net subject cutout → union with deterministic gem/metal core
(yellow-chroma HSV 18–38 / sat>90 + bright-low-chroma metal) → surgical scrub of
the mapped see-through hole and velvet slivers → alpha solidify (50→190) →
composite at 57% frame height on a programmatic charcoal studio gradient
(radial key upper-left, base 26/255), ellipse contact shadow (soft + core,
neutral-blue biased), white-balance-grade + mild S-curve + 0.6% grain.
No AI redrew a single product pixel.

## Image B — Museum Treasure
1) ENVIRONMENT PLATE (reference 141 in): "ENVIRONMENT GENERATION TASK … keep this
ring EXACTLY … rectangular landscape yellow agate (aspect about 1.4:1, NOT
square) … CHANGE ONLY THE SURROUNDINGS: dark museum display, archival charcoal
fabric, hairline brass edge, one precise warm spotlight, silent deep-black
background…"
   → result had a GOLD ring = FAIL (fidelity).
2) REMOVAL PASS (on the raw plate): "Remove the ring and its shadow completely …
fill with continuous realistic fabric texture, keep lighting/grain/composition."
3) ASSEMBLY (deterministic): real 141 ring pixels warped (scale = AI stone
length/245, no rotation) onto the empty plate; chroma-matched relight
(gain per-channel-clamped, highlights protected), ellipse contact shadow,
grain continuity. Retry count 1.

## Image C — Persian Architectural Light
Same three-step protocol. Removal prompt: "…fill with continuous realistic stone
texture, continuing the geometric shadow pattern naturally…" Assembly identical;
warm-scene relight; honey hue preserved. Retry count 1 (attempt 1 drifted the
AI stone to 2.29:1 = FAIL).

## Image D — on-hand lifestyle
Attempt 1 (FAIL — stone rendered with vertical stripes): "photorealistic adult
MALE hand … exactly five fingers … THE RING (references) … rectangular landscape
honey-yellow agate, wider than tall, NOT square … saw-tooth bezel, pierced
scrollwork … dark charcoal suit cuff, warm side light, shallow depth of field."
Retry 1 — one variable changed (stone appearance made critical):
"CRITICAL STONE APPEARANCE: smooth translucent HONEY-YELLOW chalcedony … ONE
single soft pale creamy swirl band curving diagonally across the upper face —
NO vertical stripes, NO banding lines…" → PASS.

## Global negative (applied to every generative call)
square gemstone, wrong stone proportions, rotated ring, different viewing angle,
redesigned ring, modified band, altered gemstone, changed stone color/pattern,
invented engraving, missing inscription, extra stones, fake jewelry, plastic
metal, morphed product, floating ring, cropped ring, rough cutout, pasted look,
mismatched shadows, impossible reflection, human face, female hand, extra
fingers, deformed hand, mannequin, text, price, watermark, logo, pink/purple
background, kitsch, cartoon, CGI look.
