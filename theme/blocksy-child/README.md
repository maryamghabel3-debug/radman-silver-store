# Blocksy Child Theme — RADMAN SILVER 925 (`blocksy-child`)

Official custom Blocksy child theme for **RADMAN SILVER 925** e-commerce store (`radmansilver.ir`, `staging.radmansilver.ir`).

## Brand Colors
- **Body Background:** Matte Black (`#0B0B0E`)
- **Text Color:** Ivory (`#FAF7F2`)

## Deployment via WP-CLI on Server
To deploy and activate on `staging.radmansilver.ir`:
```bash
wp theme install blocksy --activate
mkdir -p /home/radmansi/staging.radmansilver.ir/wp-content/themes/blocksy-child
# Copy style.css and functions.php into wp-content/themes/blocksy-child/
wp theme activate blocksy-child
```
