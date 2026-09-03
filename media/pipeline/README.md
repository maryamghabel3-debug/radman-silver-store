# Radman Image Pipeline v1 — media/pipeline (drafts, NOT approved)

Pilot branch `ai-media-cleaning-pilot-20260829`.

Nothing in this folder is owner-approved media. Approved outputs live under `media/approved/`
and are only written after the owner's approval command (`خوبه، برو بعدی`).

## Run log

| Run | Date | Product | Angle | Release | Status |
|---|---|---|---|---|---|
| 1 | 2026-09-03 | 384 (SKU 17224539) | A | media-image-pipeline-v1-p384-a | awaiting owner review |

## Per-run files

- `selected-product-{id}-angle-{x}.md` — why the product/angle was chosen.
- `qa-report-{id}-angle-{x}.md` — per-output QA records (ORIGINAL_REATTACHED, VIEWPOINT, RING_IDENTITY, BAND_CLOSED, HAND_SIDE, STATUS).
- `image-pipeline-state.json` — draft state (approved state is maintained at `media/approved/image-pipeline-state.json`).

## Package

Each angle ships as a pre-release asset: `radman-image-pipeline-v1-product-{id}-angle-{A|B}.zip`
(step1-no-watermark.webp, step2-black-background.webp, step3-luxury-promo.webp,
step4-on-finger.webp, contact-sheet.jpg, selected-product.md, qa-report.md).
