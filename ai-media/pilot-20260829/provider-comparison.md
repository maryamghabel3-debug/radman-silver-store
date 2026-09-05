# Provider / Method Comparison — Watermark Cleaning (Pilot, 2026-08-29)

Tested on the 8 watermarked pilot images (1600×1600). Methods compared on identical
masks produced by detector v3. Visual verdicts from zoomed before/after audits
(`contact-sheet-cleaning-before-after.jpg`, `scratch/maskqa/methodcmp/`).

| Method | Watermark removal | Product fidelity | Gemstone fidelity | Avg time / image | Est. cost / image | Strengths | Weaknesses |
|---|---|---|---|---|---|---|---|
| OpenCV Telea (INPAINT_TELEA, r=7) | Partial — pale ornamental halo ghosting | Untouched outside mask | Untouched | ~0.25 s | USD 0 | Fast, deterministic, bit-exact outside mask | Smears on textured/gradient surfaces |
| OpenCV Navier-Stokes (r=5) | Partial — ghost traces | Untouched outside mask | Untouched | ~0.20 s | USD 0 | Smooth gradients | Glossy streak artifacts |
| OpenCV xphoto **ShiftMap** | Full | Untouched outside mask | Untouched | ~11 s | USD 0 | Structure-aware patch copy | Visible blocky seams on leather/cushion textures → rejected |
| OpenCV xphoto **FSR_FAST** (chosen) | **Full — incl. pale gold frame** | **Untouched outside mask (verified bit-identical)** | Untouched | 1.6–6.7 s (avg ~3 s) | USD 0 | Clean texture continuation, seam-free after feather blend, fully local/auditable | Slight local softening where fill crosses strong edges (cushion edge, shadow band, reflection) |
| Generative diffusion inpainting (canonical prompt in `prompts-used.md`) | Not used for cleaned masters | Not guaranteed — cannot prove pixel-exactness | Risk of pattern reinterpretation | n/a | ~0.01–0.08 USD/img (typical API pricing) | Best realism for large/complex holes | **Violates the pilot's "outside-mask unchanged" guarantee; product-detail hallucination risk; needs per-image human review** |

## Other tools used in the pilot (all local, USD 0)
- **U²-Net (rembg)** — product cutouts for experiments; clean ring segmentation,
  cushion "tongue" needed manual polygon erase (auditable grids in `scratch/`).
- **ISNet general-use** — OOM in 4 GB sandbox, not evaluated.
- **Pillow + Raqm + Vazirmatn** — deterministic RTL Persian overlay.

## Recommended production method (for the remaining 221 images)
1. Run detector v3 + reviewed windows + **FSR_FAST** (batch ≈ 2 s/image, USD 0).
2. Controls and any image whose mask window cannot be verified → no-op + REVIEW.
3. Cases where the logo overlaps the ring, stone, engraving or band → keep original,
   mark REVIEW (none of the 8 pilot cases required this).
4. Optional: A/B a generative inpaint (canonical prompt) on non-overlap cases only,
   judged against FSR output by the owner before any production use.
5. Human spot-check class: shadow-band and reflection-zone fills
   (pilot instances: product-390, product-278, product-214).
