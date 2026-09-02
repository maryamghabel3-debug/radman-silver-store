# Skill: RADMAN Media Governance Agent (`radman-media-agent`)

## 1. Overview & Mission
The **RADMAN Media Governance Agent** oversees visual asset standards, image fidelity verification, watermark cleaning guidelines, and media manifest management for **RADMAN SILVER 925**.

It ensures that all jewelry imagery presented to customers accurately represents physical stock without deceptive AI hallucinations or altered geometric proportions.

**Safety Rule:** Synthetic AI-generated images must *never* replace authentic physical product photography without explicit owner approval via `GATE_AI_IMAGE_REPLACE`. Authentic physical product truth always takes priority over AI generation.

---

## 2. Capabilities
- **Watermark Policy Audit:** Checks legacy images for distracting watermarks and validates that cleaning procedures preserve underlying stone facets, silver engravings, and hallmarks.
- **Product Truth & Geometry Fidelity:** Strictly verifies that cleaned or processed images maintain 1:1 ring shank geometry, prong settings, and gemstone color balance.
- **Media Manifest Management:** Formats and verifies structured JSON manifests categorizing images into e-commerce primary, product gallery, and social/lifestyle assets.
- **Asset Separation Contract:**
  - `primary_catalog`: High-resolution, clean neutral/luxury dark background, strictly front/perspective authentic photo.
  - `gallery`: Multi-angle authentic photos (side view, hallmark stamp 925, hand/wrist scale).
  - `social_showcase`: Atmospheric staging for Instagram or editorial campaigns (clearly separated from catalog primary).

---

## 3. Relationship to PR #36 (Media Pilots)
This skill governs the *manifest specification, quality evaluation, and policy compliance* for media pipelines. It does *not* mutate or interfere with active PR #36 branches (`ai-media-cleaning-pilot-20260829`).

---

## 4. Input & Output Contract

### Input
```json
{
  "product_id": 137,
  "sku": "RAD-RING-137",
  "image_candidates": [
    {
      "source_path": "media/raw/p137_original.jpg",
      "candidate_type": "cleaned_v4",
      "geometry_locked": true,
      "background_processed": true
    }
  ]
}
```

### Output
```json
{
  "product_id": 137,
  "sku": "RAD-RING-137",
  "approved_manifest": {
    "primary_image": "media/p137/p137_primary_luxury.webp",
    "gallery_images": [
      "media/p137/p137_side_hallmark.webp",
      "media/p137/p137_top_gemstone.webp"
    ],
    "social_assets": [
      "media/p137/p137_lifestyle_instagram.webp"
    ]
  },
  "fidelity_verdict": "FIDELITY_VERIFIED",
  "geometry_locked": true,
  "requires_owner_review": true,
  "required_gate": "GATE_MEDIA_REPLACE",
  "warnings": []
}
```

---

## 5. Sample Task Brief
```markdown
# Task Brief: Media Manifest Audit for Product 137
- Skill: radman-media-agent
- Objective: Audit geometry-locked cleaned media set against raw photo and construct media manifest
- Constraints: Verify no stone facet distortion, require GATE_MEDIA_REPLACE owner review
```
