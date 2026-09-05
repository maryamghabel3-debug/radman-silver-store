# Approval Summary — Product 229 (FINAL, fully approved)

**Product:** 229 · **SKU:** NM-3597 · **Attachments:** 230 (angle A), 231 (angle B)
**Title:** انگشتر نقره مردانه الکساندریت (Men's silver ring with alexandrite)
**Storage date:** 2026-09-03
**Source release:** [media-single-ring-light-v4](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-single-ring-light-v4) — asset `radman-next-ring-multi-angle-pilot-v2.zip` (sha256 `593d089d6804b0200f5ff677a2abb89a646ca2b4a858bdce38a20df933604fde`, verified before extraction)
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## ✅ Owner decision

Product 229 owner-approved on 2026-09-03. All 8 images READY.
Angle A = right-facing ring, angle B = left-facing ring.
Bands closed, viewpoints preserved, ring identity intact.

`APPROVED_OUTPUTS=step1,step2,step3,step4` for **both** angles. Nothing for this product remains pending or in review.

## Angle coverage — complete

| Angle | Role | attachment_id | Original filename | Processed |
|---|---|---|---|---|
| A | featured | 230 | `product-229-sku-NM-3597-featured-attachment-230.webp` | ✅ 4/4 steps |
| B | gallery-1 | 231 | `product-229-sku-NM-3597-gallery-1-attachment-231.webp` | ✅ 4/4 steps |

All originals for this product_id are covered (2 of 2).

## Approved outputs and storage

Files were copied byte-for-byte from the release archive (one file extracted and committed at a time; blob SHA verified after each commit).

| Angle | Source output (release ZIP) | Stored as | wordpress_action |
|---|---|---|---|
| A | pilot/angle-A/step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| A | pilot/angle-A/step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | `replace_featured_image` |
| A | pilot/angle-A/step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| A | pilot/angle-A/step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |
| B | pilot/angle-B/step1-no-watermark.webp | `ecommerce/original-clean-b.webp` | `add_gallery_image` |
| B | pilot/angle-B/step2-black-background.webp | `ecommerce/main-black-bg-b.webp` | `add_gallery_image` |
| B | pilot/angle-B/step3-luxury-promo.webp | `gallery/luxury-promo-b.webp` | `add_gallery_image` |
| B | pilot/angle-B/step4-on-finger.webp | `gallery/on-finger-b.webp` | `add_gallery_image` |

## Rejected outputs

None. All eight outputs are approved for website use.

## ✅ Permanent rules — verified per output (from the release QA report)

| Angle | Att | ORIGINAL_REATTACHED | VIEWPOINT_UNCHANGED (step1/2) | RING_IDENTITY_PRESERVED | BAND_CLOSED | HAND_SIDE (step4) | Status |
|---|---|---|---|---|---|---|---|
| A | 230 | YES | YES | YES | YES | RIGHT | 4/4 READY |
| B | 231 | YES | YES | YES | YES | LEFT | 4/4 READY |

- **Closed band:** RADMAN rings are always closed-band; any apparent opening in an original is only the display box hiding part of the shank. The earlier open-band renders on angle B (step1/step2/step3) were regenerated as closed shanks before approval.
- **Viewpoint preserved:** angle B step1/step2 were redone as strict masked in-place edits after an earlier full re-render had drifted the three-quarter side view to a front view. Angle A step1/step2 were verified unchanged against their original.
- **Original re-attached:** the real original of each angle (attachments 230 / 231, re-downloaded from `media-originals-v1`) was attached before every generation call. No generated output was ever used as a product reference.
- **Hand rule:** angle A (right-facing) → adult male RIGHT hand; angle B (left-facing) → adult male LEFT hand. Opposite hands confirmed.

## Product identity lock

Faceted oval alexandrite (pinkish-red upper zone, olive-gold lower zone, bright specular flash) · yellow-gold crown bezel with a dense row of triangular prongs · blackened silver filigree shoulders with scrollwork and granulation · plain polished silver band, complete closed continuous shank.

## Intended WordPress action

To be executed later by the WordPress host from `apply-manifest.tsv`. **No WordPress or hosting change has been made.**

- `ecommerce/main-black-bg-a.webp` → `replace_featured_image` (featured image for attachment 230)
- all other seven images → `add_gallery_image`

## Process constraints observed

- Source archive downloaded from the release, SHA-256 verified, each image extracted alone and committed immediately (one image per commit), archive deleted afterwards.
- Output format unchanged from the approved release: WebP quality 90, 1024×1024.
- Work confined to branch `ai-media-cleaning-pilot-20260829`; `main` untouched.
- No WordPress or hosting-server modification. Pull request #36 **not merged**.
