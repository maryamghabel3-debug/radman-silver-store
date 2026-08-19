# RADMAN SILVER 925 — Static Assets

This directory holds static branding assets and font copies for reference.
The files that actually get deployed to WordPress live in
`theme/blocksy-child/` (fonts + CSS) and are synced by the runners
(`scripts/build_staging_storefront.sh`, `scripts/apply_design_system.sh`).

## `branding/`

Approved Persian RADMAN logo suite copied from `brand-assets` repo
(`maryamghabel3-debug/brand-assets:radman-silver/APPROVED-FA/` and
`radman-silver/APPROVED/` and `radman-silver/final-selected/`).

| File | Use |
|---|---|
| `radman-logo-header-black.png` | Primary header logo (matte black on transparent / light ivory surface). Deployed as `custom_logo`. |
| `radman-logo-header-black.svg` | Vector master for header (black/ivory). |
| `radman-logo-header-ivory.png` | Inverted (ivory on transparent) variant for future dark header variant. |
| `radman-logo-header-ivory.svg` | Vector master (ivory). |
| `radman-monogram-512.png` | Monogram badge. Used as site icon (favicon) source. |
| `radman-monogram-ivory-512.png` | Ivory-on-black monogram. |
| `radman-monogram.svg` | Vector monogram. |
| `logo-icon-512.png` | Final-selected favicon / PWA icon (512×512). Deployed as `site_icon`. |
| `favicon-32.png` | 32×32 favicon fallback. |
| `favicon.ico` | ICO favicon fallback. |
| `apple-touch-icon-180.png` | Apple touch icon (180×180). |

## `fonts/`

Mirrors `theme/blocksy-child/fonts/` (local WOFF2 only; no remote Google
Fonts). See `theme/blocksy-child/fonts/OFL-Estedad.txt` and
`OFL-Vazirmatn.txt` for SIL Open Font License 1.1 notices.

- **Estedad** by Amin Abedi — https://github.com/aminabedi68/Estedad
- **Vazirmatn** by Saber Rastikerdar — https://github.com/rastikerdar/vazirmatn
