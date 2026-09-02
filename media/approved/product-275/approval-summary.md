# Approval Summary — Product 275

**Product:** 275 · **SKU:** NM-3582
**Title:** انگشتر نقره مردانه عقیق سرخ ظریف (Men's silver ring, fine red agate)
**Date:** 2026-09-02
**Pilot release:** [media-single-ring-light-v2](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-single-ring-light-v2)
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## Owner approval

Storage of the product 275 approved outputs was directed by the owner in the workflow update of 2026-09-02 (TASK A: "Finish product 275 approval storage if not already done"). All four pilot outputs for the processed angle were QA READY and are stored for website use.

`APPROVED_OUTPUTS=step1,step2,step3,step4` (angle A only — see the angle coverage note below)

## ⚠️ Angle coverage — incomplete

Product 275 has **two** original images in `manifest.tsv`:

| Angle | Role | attachment_id | Original filename | Processed? |
|---|---|---|---|---|
| **A** | featured | **276** | `product-275-sku-NM-3582-featured-attachment-276.webp` | ✅ Yes — full 4-step pipeline |
| **B** | gallery-1 | **277** | `product-275-sku-NM-3582-gallery-1-attachment-277.webp` | ❌ **No** |

The product 275 pilot was produced **before** the multi-angle rule was introduced, so only angle A was processed. **Angle B (attachment 277) has not been generated, reviewed or stored.** Because the workflow permits only one product per run, angle B was not processed in this run either — it requires a dedicated follow-up run.

The `apply-manifest.tsv` carries an explicit `review_only` / `NOT_PROCESSED` row for attachment 277 so the WordPress apply step cannot mistake it for approved media.

## Approved outputs and storage (angle A)

| Source output | Stored as | wordpress_action |
|---|---|---|
| angle-a/step1-no-watermark.webp | `ecommerce/original-clean-a.webp` | `add_gallery_image` |
| angle-a/step2-black-background.webp | `ecommerce/main-black-bg-a.webp` | `replace_featured_image` |
| angle-a/step3-luxury-promo.webp | `gallery/luxury-promo-a.webp` | `add_gallery_image` |
| angle-a/step4-on-finger.webp | `gallery/on-finger-a.webp` | `add_gallery_image` |

## Rejected outputs

None. All four angle-A outputs were QA READY.

## Intended WordPress action

To be executed later by the WordPress host from `apply-manifest.tsv`. **No WordPress or hosting change has been made.**

- `ecommerce/original-clean-a.webp` → `add_gallery_image`
- `ecommerce/main-black-bg-a.webp` → `replace_featured_image` (for attachment 276)
- `gallery/luxury-promo-a.webp` → `add_gallery_image`
- `gallery/on-finger-a.webp` → `add_gallery_image`
- attachment 277 → `review_only`, nothing to apply

## QA notes

- All four outputs were generated directly from the angle-A original (`...featured-attachment-276.webp`, 1600×1600). No output was used as the product reference for another output.
- **step1** — gold "نقره مشهد" emblem fully removed, white leather box texture cleanly reconstructed; ring, gemstone, box, pink background, angle and crop preserved.
- **step2** — watermark removed, background swapped to deep charcoal black, white display box correctly kept white; stone colour/highlight, prong count, shoulder scrollwork and open band gap all match.
- **step3** — dark still-life; no hands, text, logo or watermark. Band renders as a continuous shank rather than the open adjustable band; accepted per the owner's final decision that the band interpretation is correct.
- **step4** — adult male hand, anatomy, finger count and ring scale verified correct; no face, text, logo or watermark.
- Output format: WebP quality 90, 1024×1024.

## Process constraints observed

- One product per run.
- Source ZIP deleted immediately after extracting the needed originals.
- No WordPress or hosting-server modification.
- Pull request #36 **not merged**.
