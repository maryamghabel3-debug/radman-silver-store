# Approval Summary — Product 232

**Product:** 232 · **SKU:** NM-3596 · **Attachment:** 233
**Title:** انگشتر نقره مردانه آماتیست طبیعی دامله (Men's silver ring, natural amethyst cabochon)
**Date:** 2026-09-02
**Pilot release:** [media-single-ring-light-v1](https://github.com/maryamghabel3-debug/radman-silver-store/releases/tag/media-single-ring-light-v1)
**Pull request:** [#36](https://github.com/maryamghabel3-debug/radman-silver-store/pull/36) — not merged

---

## Owner approval text

> Owner approved the generated images.
>
> Store ONLY the approved final images in GitHub under:
> media/approved/product-{id}/ ecommerce/ gallery/ social/
> Also create: media/approved/product-{id}/apply-manifest.tsv
> Do not merge. Do not touch WordPress. Return the GitHub paths and release/PR link.

**Interpretation:** "the generated images" was taken to mean all four pilot outputs. `APPROVED_OUTPUTS=step1,step2,step3,step4`.

## Approved outputs

| Source output | Stored as | QA status |
|---|---|---|
| step1-no-watermark.webp | `ecommerce/original-clean.webp` | READY |
| step2-black-background.webp | `ecommerce/main-black-bg.webp` | READY |
| step3-luxury-promo.webp | `gallery/luxury-promo.webp` | REVIEW |
| step4-on-finger.webp | `social/on-finger.webp` | REVIEW |

## Rejected outputs

None. All four pilot outputs were approved.

## Intended WordPress action

To be executed later by the WordPress host using `apply-manifest.tsv`. **No WordPress or hosting change has been made by this step.**

| Approved file | wordpress_action | Effect |
|---|---|---|
| `ecommerce/original-clean.webp` | `add_gallery_image` | Add as an additional product gallery image |
| `ecommerce/main-black-bg.webp` | `replace_featured_image` | Replace the featured image for attachment 233 |
| `gallery/luxury-promo.webp` | `add_gallery_image` | Add as a campaign/gallery image |
| `social/on-finger.webp` | `add_social_asset_only` | Store as a social asset only — do not attach to the product gallery |

## QA notes

- All four outputs were generated **directly from the extracted original** (`product-232-sku-NM-3596-featured-attachment-233.webp`, 1600×1600). No output was used as the product reference for another output.
- **step1** — old gold "نقره مشهد" watermark fully removed, white leather box texture cleanly reconstructed. Ring, gemstone, box, pink background, angle and crop preserved. Pixel-faithful.
- **step2** — watermark removed and background swapped to deep charcoal black. White display box correctly kept white. Amethyst banding, specular highlight, gold crown prong count and filigree shoulder scrollwork all match. Safest main ecommerce master.
- **step3** — ⚠️ known deviation: the real ring has an **open, adjustable band with a visible gap**; this render closes it into a continuous shank, and the amethyst reads slightly more translucent. Recognisable as the same product but **not geometry-exact**. Approved for gallery/campaign use only; must never become the main ecommerce image.
- **step4** — ⚠️ anatomy, finger count and ring scale verified correct; no face, text, logo or watermark. Fine shoulder filigree is less resolvable due to the top-down worn angle. Approved for social/Instagram use only.
- Output format: WebP quality 90, 1024×1024.

## Process constraints observed

- Only this one product was processed; the full catalogue was not touched.
- Source ZIP deleted immediately after extracting the single original image; peak disk usage ~3 MB against a 200 MB budget.
- No WordPress or hosting-server modification.
- Pull request #36 was **not merged**.
