# Website Showcase — Style Recommendation (product 211, 2026-08-29)

## Selected product
Men's natural amethyst 925 silver ring — product **211**, SKU **NM-3603**, attachment **212**,
1600×1600 cleaned source (Pilot V2, READY). Full selection rationale: `selected-product.md`.

## Generation method
AI-native generation with the cleaned real photograph as the ONLY product reference
(same capability that produced the owner-approved lifestyle images). Camera angle kept
at the source orientation (slightly above, front three-quarter) so no unseen geometry
was invented. No cutout, no paste, no compositing — each output is one coherent
photograph. 0 retries needed; 6/6 styles passed QA on first generation.

## QA results (qa/website-showcase-qa.csv)
All six styles READY. Shared fidelity observations:
- Ring silhouette, crown prongs, beaded bezel, floral shoulder engraving and the
  "925" inner stamp preserved in all six outputs.
- Amethyst hue and internal character preserved; pattern reads identically at
  catalog scale (see `qa/contact-sheet-product-fidelity.jpg` for close-ups).
- No cutout appearance, no floating product, no broken edges anywhere.

Style-specific observations for owner attention:
- **05 leather:** warm key gives the silver a mild bronze cast (physically consistent
  with a warm-lit leather scene; stone unaffected). Confirm brand fit.
- **06 museum:** spotlight lifts the amethyst slightly toward lavender.
- **03 ivory:** amethyst reads marginally brighter under the bright key.

## Recommendations
- **Best main WooCommerce image:** STYLE 6 — Museum Gradient (most neutral, timeless,
  best product separation; pairs with any theme) — close second: Style 1 (more mood,
  still very clean).
- **Best gallery styles:** Style 1 (dark charcoal velvet) + Style 4 (graphite slate) +
  Style 3 (ivory stone) — dark/light alternation shows the ring in varied contexts.
- **Best category thumbnail:** Style 3 (ivory stone) — brightest, highest contrast
  against typical theme backgrounds; reads clearly at small sizes. (Style 6 equally
  strong if the store keeps a dark theme.)
- **Standardization across 100 products:** all six styles are scene-templates with a
  fixed recipe (same light logic, angle lock, fidelity negative prompt) → any subset
  can be standardized. Style 6 is the most automatable (no surface texture to match);
  Styles 1/3/4 close behind; Style 2 needs per-ring reflection QA.
- **Multiple styles in one gallery:** yes, safely — the ring identity is consistent
  across outputs (verified in fidelity sheet). Recommended pattern: 1 main (Style 6)
  + 2–3 gallery styles per product; keep real macro photos of engravings/stone in the
  gallery as authenticity anchors.

## Production estimate (231 images)
- ~2–3 min per image including QA review → ≈ 8–12 hours agent time total;
  realistic batch: 30–40 images/day with per-image fidelity QA.
- Style variety multiplies outputs if desired (e.g., 2 styles × 100 products = 200 renders).

## External API cost
**USD 0.00** — produced entirely with the agent's native image-generation capability.
No external paid API was called. Budget respected (USD 0.00 cap).
