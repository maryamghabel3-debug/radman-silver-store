# site-gallery-export

Byte-for-byte transfer package for the site gallery (branch `ai-social-luxury-20260911`).
**No source image was regenerated, edited, re-encoded, renamed or overwritten.** Every file under
`step3/` and `step4/` is a byte-identical copy of the file named in `source_path` (verified by sha256).

## Contents
- `step3/` — Step3 images that are **not yet on the site** → `deployment_action=APPEND_TO_GALLERY_AFTER_APPROVAL`
- `step4/` — on-hand shots (**candidates**) → `deployment_action=HOLD_PENDING_OWNER_REVIEW`
- `review/step3-contact-sheets/`, `review/step4-contact-sheets/` — preview sheets only (they never modify originals)
- `manifest.json` / `manifest.csv` — one row per file with identity, provenance, hashes and status
- `CHECKSUMS.sha256` — sha256 of every file in this package

## Rules applied
1. Candidates, FAILED_QA items, rejected pose-fix files and versions with unclear identity are **not** counted as final.
2. `GENERATED` in a manifest is **not** owner approval — only the owner approves.
3. Identity comes from `product_id` + SKU (WooCommerce store API) and the branch manifests; `?p=ID` redirects were not used.
4. The 42 Step3 images already attached to the site are **not** re-added: they carry
   `qa_status=KNOWN_ALREADY_ATTACHED` and `deployment_action=SKIP_KNOWN_ALREADY_ATTACHED`.
5. The legacy `luxury-promo` attachment of 10 products does **not** mean they are in the gallery, so those products
   were **not** skipped automatically. None of them has a verified Step3/Step4 source file on this branch.
6. Gallery order: keep the current main/gallery image → append the new Step3 images → then the new Step4 images.
7. Nothing was pushed to `main`, no site/live connection was made, no original image was changed.

## Statuses used
`OWNER_APPROVED` · `PENDING_OWNER_REVIEW` · `FAILED_QA` · `AMBIGUOUS_IDENTITY` · `KNOWN_ALREADY_ATTACHED`

## Deployment is gated
No action may be taken on the site until the owner reviews the contact sheets and writes exactly
`APPROVE_STEP3_STEP4_SITE_DEPLOY`.

## Archives
`step3-site-export.zip` and `step4-site-export.zip` (split into `part-aa`, `part-ab`, … when larger than 20 MB).
Re-join and verify with:
```bash
cat step4-site-export.zip.part-* > step4-site-export.zip
sha256sum -c CHECKSUMS.sha256 --ignore-missing
unzip -t step4-site-export.zip
```
