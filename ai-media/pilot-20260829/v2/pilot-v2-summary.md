# RADMAN SILVER 925 — Pilot V2 Summary (2026-08-29)

## Status
Owner feedback on Pilot V1 fully applied. V2 contains:
- `cleaned/` — 10 files, original filenames preserved:
  - 9 unchanged V1-cleaned images (owner-approved)
  - 1 repaired: `product-117-sku-1009-gallery-1-attachment-119.webp` (product 117, SKU 1009, attachment 119)
- `social/ai-native/posts/` — 3 Instagram posts, 1080×1350, text-free, logo-free
  - product-184 DARK FORMAL · product-211 WARM LEATHER · product-300 CLEAN PREMIUM
- `social/ai-native/stories/` — 3 Instagram stories, 1080×1920, text-free, logo-free (same three rings/styles)
- `qa/qa-report-v2.csv`, `qa/contact-sheet-cleaning-v2.jpg`, `qa/contact-sheet-social-v2.jpg`
- `owner-feedback-applied.md`, `pilot-v2-summary.md`

## Excluded per owner decision
experiments/, old cutout-based posts, video/, cutout PNGs, GrabCut/rembg outputs,
alpha-mask composites, paste-composites. No video. No Radman logo anywhere.

## Method
- Repair 119: AI generative fill (native image-editing capability) with reviewed
  repair polygon; ring/stone/inscriptions excluded from the mask and verified
  unchanged (max-diff = 1 outside mask; ring pixels untouched by construction).
- Social: AI-native generation with each cleaned master as the only product
  reference (the method the owner approved via the male lifestyle images).
  Three visual directions (A dark formal / B warm leather / C clean premium),
  masculine adult hand, coherent single photographs. Fidelity QA per asset in
  `qa/qa-report-v2.csv` — 6/6 READY, 0 FAILED. Retry policy: none of the six
  social assets needed a retry; the 119 repair used 1 of 3 allowed retries.

## Known notes for owner review
- product-184 post: part of the band engraving is naturally occluded by the
  finger at the chosen angle (not an alteration).
- Social masters are text-free by policy; Persian campaign text should be added
  at publication time (deterministic overlay, Vazirmatn RTL) per project policy.

## Next action
WAIT_FOR_OWNER_REVIEW — production run (~221 images) not started.
