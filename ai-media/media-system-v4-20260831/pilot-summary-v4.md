# RADMAN SILVER 925 — Pilot Summary v4 (2026-08-31)

## Objective
Owner-approved Round-3 art direction, rebuilt under the new GEOMETRY LOCK
protocol after Round-3 failed on stone shape (square vs rectangular) and viewing
angle. Market-research-driven 4-image media set for one product (P137).

## What was built
| Image | Role | Technique | Geometry (oriented/bbox dev) | Status |
|---|---|---|---|---|
| A-main-ecommerce | purchase reference | 100% real pixels + programmatic studio | 1.2% / 0.0% | READY |
| B-campaign-museum | gallery campaign | AI empty-plate + real-pixel composite | 4.3% / 5.3% | READY |
| C-campaign-persian-light | gallery campaign | AI empty-plate + real-pixel composite | 2.3% / 3.3% | READY |
| D-onhand-lifestyle | gallery lifestyle | generative (male hand) | on-hand foreshortening; visual pass | READY |

## Key events
- geometry-spec.md created from measured real pixels (att 141): stone 1.556
  oriented / 1.388 bbox, REF angle 149.6°, band ≈0.38× stone length.
- Deterministic cutout pipeline iterated 4× (velvet slivers, butterfly mask,
  white-box flood) until QC was clean on black/white/charcoal.
- B attempt 1: AI turned the ring GOLD → fail. C attempt 1: stone 2.29:1 → fail.
  Both retried via ring-removal empty plates + real-pixel composites → PASS.
- D attempt 1: striped stone → fail; retry with one variable changed → PASS.
- Numeric QA: qa/media-system-v4-qa.csv + stone-measurements.json; visual
  evidence: contact-sheet-media-system-v4.jpg, contact-sheet-geometry-check.jpg
  (aspect numbers printed outside images).

## Total generative retries: 3 (B 1, C 1, D 1) — all within the ≤3 limit.
## External paid API cost: USD 0.00. No video, no WordPress changes, PR #36 updated, not merged.
