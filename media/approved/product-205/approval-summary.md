# Approval Summary — Product 205 (FINAL, fully approved)

**Product:** 205 · **SKU:** NM-3605
**Title:** انگشتر نقره مردانه عقیق باباقوری (Men's silver ring, babaghori agate)
**Date:** 2026-09-02
**Pilot release:** [media-single-ring-light-v3](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-single-ring-light-v3)
**Hand fix release:** [media-product-205-hand-fix-v1](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-product-205-hand-fix-v1)
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## ✅ Owner decision

**Product 205 is fully approved by the owner.** All eight outputs across both angles may be used on the website. Nothing for this product remains in pending or review status.

Owner's final decision:

> 1. Fix product 205 first.
> 2. Then store product 205 as approved.
> 3. Then move to the next ring.
> 4. Do not leave product 205 in pending/review status after this run.

## ✅ Left and right hand rule satisfied

| Angle | Attachment | Ring orientation | Hand used | Required | Correct |
|---|---|---|---|---|---|
| A | 206 | right-facing | **RIGHT** male hand | RIGHT | ✅ |
| B | 207 | left-facing | **LEFT** male hand | LEFT | ✅ |

The two worn shots use **opposite hands**. Angle A's step4 was regenerated in this run to premium masculine lifestyle quality (dark tailored suit cuff, warm controlled commercial lighting, shallow depth of field); angle B's step4 was already good and was kept unchanged. Ring identity — the honey/caramel agate cabochon with pale cream banding, the all-silver claw prong setting, the openwork silver shoulders, no gold — is preserved in both.

## Angle coverage — complete

Product 205 has exactly **two** originals in `manifest.tsv` and **both were fully processed** through all four steps:

| Angle | Role | attachment_id | Original filename | Processed |
|---|---|---|---|---|
| A | featured | 206 | `product-205-sku-NM-3605-featured-attachment-206.webp` (1600²) | ✅ 4/4 steps |
| B | gallery-1 | 207 | `product-205-sku-NM-3605-gallery-1-attachment-207.jpg` (2560²) | ✅ 4/4 steps |

## Approved outputs and storage

| Source output | Stored as | wordpress_action |
|---|---|---|
| angle-A/step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| angle-B/step1-no-watermark.webp | `ecommerce/original-clean-b.webp` | `add_gallery_image` |
| angle-A/step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | `replace_featured_image` |
| angle-B/step2-black-background.webp | `ecommerce/main-black-bg-b.webp` | `add_gallery_image` |
| angle-A/step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| angle-B/step3-luxury-promo.webp | `gallery/luxury-promo-b.webp` | `add_gallery_image` |
| angle-A/step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |
| angle-B/step4-on-finger.webp | `gallery/on-finger-b.webp` | `add_gallery_image` |

**All outputs may be used on the website.**

## Rejected outputs

None. All eight outputs are approved.

## Intended WordPress action

To be executed later by the WordPress host from `apply-manifest.tsv`. **No WordPress or hosting change has been made by this step.**

Only `main-black-bg-a.webp` carries `replace_featured_image` (for attachment 206); every other file is added as a gallery image, since a product can have only one featured image.

## QA notes

- Each angle's four steps were generated against **that angle's own original**; no output was used as a reference for another output, and the left/right views were never mixed.
- Watermark removal verified on all four `step1`/`step2` outputs; the emblem sits in a different corner per angle (lower-right on A, lower-left on B).
- Worn shots: anatomy, finger count and ring scale verified; no face, text, logo or watermark.
- Output format: WebP quality 90, 1024×1024.
- Full detail in `qa/product-205-hand-fix-report.md` and `qa/product-205-hand-fix-contact-sheet.jpg`.

## Process constraints observed

- One product stored per run; source ZIP deleted immediately after extracting the needed originals.
- No WordPress or hosting-server modification.
- Pull request #36 **not merged**.
