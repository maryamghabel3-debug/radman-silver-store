# Owner Feedback Applied — Pilot V2 (2026-08-29)

| # | Owner decision | Action taken in V2 |
|---|---|---|
| 1 | Male lifestyle images approved in principle | Method (AI-native photo with the cleaned ring as sole product reference) retained and extended to all V2 social assets. |
| 2 | Cleaned image 119 damaged (background + area under ring) — must be corrected | Identified: `product-117-sku-1009-gallery-1-attachment-119.webp` (product 117, SKU 1009, attachment 119). Damage is a **vendor pre-existing retouch smudge** (textureless velvet patch under the band + straight Hough-detected seams), preserved in V1 because the file was a no-op control. Repaired via AI generative fill (attempt 1 rejected, attempt 2 approved) composited strictly inside a reviewed polygon; outside-mask pixels unchanged (max-diff=1). Delivered as the same filename in `cleaned/`. |
| 3 | `experiments/` rejected (detached cutout look) | Excluded from V2 delivery entirely; no cutout composites shipped. Method retired. |
| 4 | `social/posts` cutout-based outputs rejected | Replaced by **AI-native photography** (one coherent photo per asset, ring referenced from the cleaned master). No paste-compositing anywhere in V2. |
| 5 | Video rejected — do not create/deliver video | No video created or included in V2. |
| 6 | No Radman logo at this stage; text-free and logo-free | All V2 social masters are text-free and logo-free. Brand A/B variants not included. |

## Image 119 repair record
- Original = source of truth; damage present in the vendor original (verified: V1 output was byte-identical to original).
- Evidence: local high-frequency texture map (damaged σ≈3 vs healthy velvet σ≈40–177), Canny+Hough straight seams (x≈554 vertical; y≈805–830 horizontal), CLAHE-enhanced quadrant audit.
- Repair: AI generative fill (retry #2) with velvet-nap regrowth instructions → feathered composite inside polygon (455,470)…(895,660), excluding ring/stone (25 px buffer + 30 px downward reflection buffer) and the white box.
- Fidelity: ring untouched by construction (outside-mask max-diff = 1); texture after repair σ≈56 under band (continuous with neighbors); no seams visible in enhanced review.
