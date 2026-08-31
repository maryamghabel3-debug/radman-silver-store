# GEOMETRY SPEC — P137 / SKU 1003 (measured from real pixels, 2026-08-31)

Source of truth: attachment 141 (cleanest full-ring real view; identical head
geometry to hero 138). Measurements computed programmatically from the original
file — not estimated.

## Gemstone outline (hard rule)
- **RECTANGULAR, landscape orientation — NOT square.**
- Oriented min-area rect of the yellow stone face: **245 × 157 px → aspect 1.556 : 1**
- Axis-aligned bounding box in the reference view: **279 × 201 px → aspect 1.388 : 1**
- Spec band for verification: oriented-aspect 1.556 ±6% (1.46–1.65) AND
  bbox-aspect 1.388 ±6% (1.30–1.47). A square rendering (≈1.0) fails instantly.
- Cut: rectangular cabochon with softly rounded corners (emerald-cut-style
  outline, no faceting), one pale swirl band across the upper face.
- Color: translucent honey-yellow chalcedony.

## Bezel
- Dense ring of small pointed saw-tooth prongs around the stone; outer rim
  edged with a thin line of tiny beads. Projected bezel band ≈ 18–22 px on a
  245 px stone length (≈8% of stone length per side).

## Band
- Broad tapering polished silver band; ornate pierced openwork scroll/filigree
  shoulders (leaf-and-vine cutouts).
- Projected band width just below the head ≈ 92 px → **band ≈ 0.38 × stone
  length** at the shoulder, tapering toward the base.
- One authentic see-through opening between head underside and shoulder.

## Ring proportion
- Full ring projected bbox in reference: **334 w × 389 h px** (taller than wide).
- Head (stone+bezel) width ≈ 334 px ≈ full ring width at top.

## Viewing angle (locked for all outputs)
- Three-quarter hero view; camera elevated ≈ 20–25° above the stone plane;
  head rotated ≈ 30° to frame-left; band descends to the lower right.
- Environment may change; the camera-to-ring relationship must not.

## Verification protocol
Every generated output is measured with the same oriented-minAreaRect +
bbox pipeline (yellow-chroma segmentation). Aspect deviation >6% on either
metric, or visible angle rotation/redesign = automatic FAIL (retry ≤3,
one variable per retry; still failing → FAILED, not delivered).
