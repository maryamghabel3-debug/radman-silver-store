# Media System v4 — Recommendation (P137, 2026-08-31)

## Did the geometry lock succeed?
**Yes — completely, via pixel-preservation.** Full regeneration failed the new
geometry bar twice (B: ring rendered gold; C: AI stone drifted to 2.29:1).
The winning technique for A/B/C:
1. Generate the ENVIRONMENT with the ring in place, then order the model to
   REMOVE the ring and shadow → clean empty plate (no ghosting, texture
   continues);
2. Cut out the REAL ring pixels from attachment 141 (u2net + deterministic
   gem/metal core + surgical hole scrub);
3. Composite the real pixels onto the empty plate (scale from stone length,
   rotation locked), chroma-match the relight, rebuild the contact shadow.

Measured aspect deviations of delivered images: **A 1.2%/0.0% · B 4.3%/5.3% ·
C 2.3%/3.3%** (spec ±6%) with viewing angle 148.9–150.3° vs reference 149.6°.
Image D is a full generation (hand cannot be pixel-preserved); its stone reads
1.38:1 under on-hand foreshortening (front-view spec not applicable at that
angle) — shape/bezel/band verified against `qa/geometry-spec.md`.

## READY for real store use
- **A-main-ecommerce.webp** — main purchase reference (real pixels).
- **B-campaign-museum.webp** — gallery 1 (approved Round-3 direction).
- **C-campaign-persian-light.webp** — gallery 2 (approved Round-3 direction).
- **D-onhand-lifestyle.webp** — gallery 3, scale/lifestyle only, never main.

## Standard media set for all ~100 products
A + B + C + D as delivered here. A must always be real-pixel; B/C use the
empty-plate + composite technique (one style call + one removal call each);
D is generative with the D-retry prompt pattern (stone appearance made critical)
and a max-3 retry ladder.

## Production estimate (4 images × 100 products ≈ 400 outputs)
- A: ≈4 min/product (deterministic pipeline) → ≈7 h
- B + C: ≈8–10 min/product (3 generative calls + assembly + QA) → ≈15 h
- D: ≈5 min/product incl. retries → ≈8 h
- Geometry QA (automated measurements + contact sheets): ≈3 min/product → ≈5 h
**Total ≈ 35 hours of agent time; external paid API cost USD 0.00** (native
capabilities only; imagegen quota is the practical constraint — ≈10 images/turn
→ ~35–40 turns for the full catalog).

## Guards that made this round pass (keep for production)
geometry-spec.md numbers in every prompt; empty-plate removal instead of
inpainting; numeric aspect measurement after every output (±6% band); failed
full-gens archived in failed/; READY status is a QA-candidate verdict only —
final approval belongs to the owner.
