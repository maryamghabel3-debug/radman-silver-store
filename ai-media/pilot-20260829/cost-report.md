# Cost Report — Media Cleaning Pilot (2026-08-29)

**Hard pilot budget: USD 5.00 — actual external spend: USD 0.00**

## External API usage
| Service | Usage | Cost |
|---|---|---|
| GitHub API (repo, release, PR) | ~20 calls | USD 0 (free tier) |
| Generative image edits (male-lifestyle tests, 4 calls incl. 1 rejected + retried) | included in agent workspace image tool — no paid third-party API key was available or used | USD 0.00 charged against pilot budget |
| Generative video API | not available → deterministic render instead (see `pilot-summary.md`) | USD 0.00 |

No paid API was authorized, therefore no paid calls were made. The lifestyle tests
were produced with the workspace's built-in image tool at no pilot cost; if these
had been run on a typical commercial API (≈ USD 0.04–0.08/image), the 4 calls would
have cost ≈ USD 0.16–0.32 — still far below the cap.

## Compute time (local, sandbox)
| Stage | Time |
|---|---|
| Watermark detection + FSR inpaint, 10 images | ~21 s total (avg 1.99 s watermarked, 0.03 s control) |
| Contact sheets / audits (231 thumbnails + zooms) | ~10 s |
| U²-Net cutouts (4 images) | ~5 s |
| Experiments build (24 assets + A/B) | ~8 s |
| Video render (150 frames 1080×1920) | ~15 s |
| **Total pipeline compute** | **< 2 min** |

## Projected production cost, remaining 221 images
- Cleaning at ~2 s/image → ≈ 7.5 min compute, **USD 0**.
- Projected deliverable zip ≈ 300–400 MB → GitHub Release asset (free).
- Optional generative lifestyle/social variants at owner's discretion — outside
  pilot budget, to be quoted separately if an API is authorized.
