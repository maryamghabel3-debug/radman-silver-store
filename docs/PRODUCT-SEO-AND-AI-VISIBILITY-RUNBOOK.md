# PR-34 — Exact Pricing and Product SEO / AI Visibility Runbook

## سیاست قیمت دقیق

قیمت Excel به‌عنوان `legacy_price` دقیقاً به تومان خوانده می‌شود. اگر وزن verified موجود باشد، `computed_floor = weight × approved_rate` و بزرگ‌ترِ دو مقدار انتخاب می‌شود. هیچ rounding روانی، 9-ending یا rounding اجباری 50000 تومانی وجود ندارد؛ فقط نتیجه اعشاری به تومان کامل بعدی ceiling می‌شود.

متادیتا:

- `radman_legacy_price_exact_toman`
- `radman_computed_floor_exact_toman`
- `radman_final_price_exact_toman`
- `radman_price_rounding_policy=EXACT_NO_CHARM_NO_50000_ROUNDING`
- `radman_price_selection_reason`

## Preview قیمت دقیق ۲۰ Draft — read-only

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --reprice-existing-exact --dry-run
```

## Apply قیمت دقیق ۲۰ Draft

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
CONFIRM_STAGING_APPLY=YES \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --reprice-existing-exact
```

runner ابتدا backup دیتابیس می‌سازد. pipeline نیز پیش از اولین mutation فایل `exact-reprice-before.csv` را ایجاد می‌کند. فقط regular/current price و pricing meta تغییر می‌کنند؛ title، SKU، description، media، category، stock و Draft status با snapshot قبل/بعد کنترل می‌شوند. `_sale_price` و sale dates حذف می‌شوند.

## SEO plan — read-only

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --seo-plan
```

## SEO enrichment + QA برای ۲۰ Draft

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
CONFIRM_STAGING_APPLY=YES \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --seo-batch-ready
```

این mode deterministic SEO enrichment، سپس QA و publication blockers را اجرا می‌کند و **هرگز publish نمی‌کند**.

## خروجی SEO

- Rank Math title/description/focus keyword؛
- short description دو تا چهار جمله؛
- image alt-text plan برای featured/gallery؛
- internal-link recommendations؛
- search entities و Woo custom attributes؛
- پنج گزارش QA تعریف‌شده در `PRODUCT-SEO-QUALITY-GATE.md`.

هیچ Product schema دوم تزریق نمی‌شود. قیمت، currency و availability ساختاریافته باید از WooCommerce و Rank Math با storefront یکسان باشند. review/rating جعلی و return/shipping markup تأییدنشده ممنوع است.

## Optional external LLM

خروجی deterministic بدون API خارجی کامل است. adapter خارجی فقط با `RADMAN_ENABLE_EXTERNAL_LLM=1` و secret خصوصی `RADMAN_EXTERNAL_LLM_API_KEY` فعال می‌شود. خروجی آن فقط Draft suggestion است، از humanization gate عبور می‌کند و verified fact یا محتوای فروشگاه را خودکار overwrite/publish نمی‌کند.
