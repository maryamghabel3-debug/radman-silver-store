# Product SEO Quality and Publication Gate

`agents/agent_product_seo_qa.py` پیش از هر تصمیم انسانی برای انتشار، هر محصول را در یکی از وضعیت‌های زیر قرار می‌دهد:

- `SEO_PASS`: همه critical checks پاس شده‌اند؛ محصول همچنان Draft است.
- `SEO_REVIEW`: critical blocker ندارد ولی review انسانی لازم است.
- `SEO_BLOCKED`: حداقل یک critical blocker وجود دارد و publication ممنوع است.

## Critical checks

- status دقیقاً Draft؛
- title عمومی بدون trailing model code؛
- SKU موجود و یکتا؛
- legacy identity موجود؛
- `_regular_price == _price` و sale price خالی؛
- category و featured image موجود؛
- description، short description، SEO title و meta description موجود؛
- technical values سازگار؛
- بدون phone/contact یا shipping/payment/warranty/return promise؛
- بدون internal system disclaimer یا generic AI phrase؛
- description/meta به‌اندازه کافی یکتا؛
- schema-visible price/currency/availability مطابق WooCommerce؛
- بدون review/rating ساختگی.

## گزارش‌های اجباری

```text
product-seo-report.csv
product-seo-report-fa.txt
duplicate-content-report.csv
schema-consistency-report.csv
publication-blockers.csv
```

`publication-blockers.csv` سند gate است. وجود هر ردیف به معنی ممنوع‌بودن publication آن محصول است. هیچ runner mode در PR-34 status محصول را به publish تغییر نمی‌دهد.

## اجرای read-only QA

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --seo-qa
```
