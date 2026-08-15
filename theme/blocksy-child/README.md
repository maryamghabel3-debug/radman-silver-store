# Blocksy Child Theme — RADMAN SILVER 925 (`blocksy-child`)

Official minimal Blocksy child theme for **RADMAN SILVER 925** (`radmansilver.ir`, `staging.radmansilver.ir`).

## Brand Palette (single source of truth)

| Role       | Value    | Token                   |
|------------|----------|-------------------------|
| Background | `#0B0B0E`| `--radman-bg-dark`      |
| Text       | `#FAF7F2`| `--radman-text-ivory`   |

## What this child theme does NOT contain

- No external Google Fonts
- No production-only tracking scripts
- No hardcoded credentials or secrets
- No unapproved brand colors
- No parent-stylesheet double-load (child CSS is enqueued with the parent handle as a dependency)

## Files

- `style.css` — theme header + palette CSS variables + base dark/ivory rules.
- `functions.php` — single enqueue action; no other runtime code.
- `README.md` — this file.

## Deployment

Deployment is performed exclusively by the reviewed staging runner:

```bash
bash scripts/radman_stage_apply.sh --plan           # default: dry run
bash scripts/radman_stage_apply.sh --apply-staging  # staging only, requires CONFIRM_STAGING_APPLY=YES
```

The runner:

1. Verifies staging-only guards (`APP_ENV=staging`, `WP_URL=https://staging.radmansilver.ir`, `blog_public=0`, no `public_html` path).
2. Creates timestamped DB + existing-child-theme backups under `RADMAN_PRIVATE_DIR/backups/`.
3. Syncs `style.css`, `functions.php`, `README.md` into `wp-content/themes/blocksy-child/`.
4. Activates `blocksy-child` and re-verifies the active theme.

Production deployment is out of scope for this repository until an explicit production cutover mission is approved.
