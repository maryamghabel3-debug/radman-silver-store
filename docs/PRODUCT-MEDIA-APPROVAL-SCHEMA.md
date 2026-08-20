# Product Media Approval Contract — Next Stage Only

This document defines the owner approval record consumed by a **future, separately approved WordPress import mission**. This mission does not import products or media.

## Required fields

| Field | Type | Rule |
|---|---|---|
| `legacy_id` | string | Public legacy product ID; required |
| `sku` | string | Final RADMAN SKU; required before import |
| `selected_source_image` | string | Owner-selected local source filename from `legacy-cache/original-images/` |
| `selected_background_variant` | enum | `matte-black`, `black-velvet-gradient`, or `dark-neutral-studio` |
| `qa_status` | enum | `PASS`, `REVIEW`, or `REJECT` from the image QA report |
| `owner_approved` | boolean | Explicit visual approval by the owner |
| `approved_for_wordpress_import` | boolean | Separate explicit approval for a later import mission |
| `notes` | string | Edge/stone/reflection concerns, crop choice, rejection reason, or retake request |

## JSON example

```json
{
  "legacy_id": "3639",
  "sku": "RAD-RNG-M-1014",
  "selected_source_image": "3639-01.jpg",
  "selected_background_variant": "matte-black",
  "qa_status": "REVIEW",
  "owner_approved": false,
  "approved_for_wordpress_import": false,
  "notes": "لبه رکاب و نگین سبز باید در contact sheet با بزرگ‌نمایی بررسی شود."
}
```

## Approval gates

A future importer must refuse the image unless all conditions are true:

1. `qa_status == PASS` (or a documented owner override after human review);
2. `owner_approved == true`;
3. `approved_for_wordpress_import == true`;
4. the selected file exists under the controlled private directory;
5. BRIA evaluation output is not selected for commercial publication;
6. the source image is owned/licensed by the owner.

`REVIEW` means a human must inspect stones, engravings, thin metal edges, reflections, and clipping. `REJECT` must never advance automatically.

New angles, lifestyle/in-hand images, and views not present in the real source set require real photography. They must not be synthesized from a single product image.
