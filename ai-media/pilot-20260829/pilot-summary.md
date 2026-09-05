# RADMAN SILVER 925 — AI Media Cleaning Pilot Summary (2026-08-29)

## Scope
- Source: GitHub Release `media-originals-v1`, asset `radman-product-images-20260829-052041.zip`
  (231 images / 100 products, SHA-256 prefix bc219415bd67c6d8).
- Pilot set: 10 images / 10 products (`pilot-selection.tsv`) — 4 simple, 2 shadow-adjacent,
  2 difficult, 2 control-clean. Full archive untouched pending owner approval.

## Watermark finding (archive-wide)
Two clean photo families (hand-worn shots; black-velvet box shots) and one watermarked
family: pink-studio series (products P175–P381, SKU `NM-35xx`/`NM-36xx`/`1218xxxx` etc.)
carrying a gold ornamental «نقره مشهد» seller logo, bottom third, near the ring base.
≈ 135 of 231 images are affected — matches the ~221-image remainder estimate.

## Cleaning pipeline (deterministic, local, USD 0)
Vivid-gold core detection → grown bbox → pale-gold capture → human-reviewed per-image
windows (`scripts/mask-review.json`) → **OpenCV xphoto FSR_FAST** inpaint with feathered
blend → numeric assertion that eroded non-mask pixels are bit-identical.
Method selection evidence: Telea/NS ghosting and ShiftMap blockiness documented in
`provider-comparison.md`; FSR chosen. Controls: detector produced empty masks; outputs
byte-identical (SHA-256 verified).

## Results
- 8/8 watermarked pilot images cleaned successfully (READY). 0 FAILED.
- Product pixels untouched everywhere; masks ≈ 2.3–5.4% of image area.
- Minor background-only softening noted on 3 images (P278 cushion edge, P390 shadow
  band, P214 reflection); P214 flagged `needs_human_review` (reflection realism).
- Controls: 2/2 CONTROL_CLEAN.

## Experiments (4 products: 211, 184, 214, 390)
Per product: `ecommerce-neutral`, `luxury-dark`, `instagram-post-4x5` (1080×1350),
`instagram-story-9x16` (1080×1920), `brand-ab-test-A/B` (B uses the official repo
monogram `assets/branding/radman-monogram-512.png`; no logo redesign; ecommerce
masters remain unbranded). Product pixels come only from cleaned masters via U²-Net
cutouts (cushion remnants removed with audited polygons; product-300 excluded from
composites because its cushion tongue crosses in front of the band — repairing it
would require inventing product pixels, which policy forbids).

## Social / lifestyle
3 male-lifestyle tests (hand-worn, suit/leather settings) for products 211, 184, 214.
product-214 first render simplified the dendritic stone pattern → rejected and
regenerated pixel-faithfully. Persian overlay demo (post) built deterministically with
Vazirmatn RTL; text-free master + editable text layer + JSON placements shipped in
`social/posts/`.

## Video
1 × 5 s vertical 1080×1920 MP4 (`video/pilot-pushin-1080x1920.mp4`), deterministic
push-in/parallax/light-drift from the approved luxury-dark master. No generative video
API was available; a generative clip would require an authorized API and per-frame
identity QA. No cost incurred.

## Compliance notes
- No token printed, committed, or logged; used only via HTTPS API calls.
- Original ZIP and extracted originals NOT committed; originals stay out of Git.
- Media delivered as Release asset `media-cleaning-pilot-v1` /
  `radman-media-cleaning-pilot-20260829.zip`; repo branch carries only scripts,
  prompts, manifests, QA reports, contact sheets and docs.
- Do-not-touch list respected: no engraving/inscription/stone-pattern edits anywhere;
  no Radman branding on ecommerce masters; no text baked into social masters.

## Next action
WAIT_FOR_OWNER_APPROVAL — do not process the remaining ~221 images before sign-off.
