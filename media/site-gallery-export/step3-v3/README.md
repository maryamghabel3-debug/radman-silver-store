# step3-site-export-v3

Transfer package for the 10 owner-approved Step3 v3 files (2026-09-17).
**No new image was generated for this package**; every file under `step3/` is a byte-identical copy of the
approved file (`sha256` in `manifest.json` and `CHECKSUMS.sha256`).

## Contents
- `step3/` - the 10 files to append: 61-B, 65-A, 65-B, 69-A, 69-B, 73-A, 73-B, 77-A, 77-B, 256-A (1080x1350, PNG)
- `deploy-step3-v3.csv` - upload list (10 APPEND rows + the 42 already-attached rows for reference)
- `manifest.json` / `manifest.csv` / `CHECKSUMS.sha256`
- `review/step3-v3-contact-sheets/step3-v3-all10.png`

## Not in this package
- Step4 (47 files) - untouched, its own approved archive stays as it is
- the 42 already-attached Step3 images - already on the site (`SKIP_KNOWN_ALREADY_ATTACHED`)
- the previous `step3-site-export.zip` (rejected files) - still marked `NOT_FOR_DEPLOY`

## Gallery order
keep the current main/gallery image -> append these 10 files (gallery_order 1..10) -> then the Step4 order.
