# راهنمای import هزار محصول جدیدتر از Excel با تصاویر اصلی

**نسخه:** PR-28

**تصمیم قطعی منبع داده:** فایل Excel مالک تنها منبع حقیقت عنوان، دسته، قیمت، موجودی، فعال بودن، وزن، کد و توضیحات است. scrape/API برای داده محصول منسوخ شده و فقط برای یافتن و دانلود gallery اصلی با `legacy_product_id` مجاز است.

## ورودی قطعی

```text
/home/radmansi/radman-deploy/products_20260821_182238.xlsx
Sheet: همه محصولات
```

ترتیب قطعی مالک:

```text
ID بالاتر = محصول جدیدتر
3643 جدیدترین ... 1 قدیمی‌ترین
```

انتخاب با `legacy_id DESC` انجام می‌شود؛ ردیف غیرفعال یا `نوع موجودی=ناموجود` حذف و سپس اولین `MAX_PRODUCTS` انتخاب می‌شود.

## API slot

مسیر رزروشده برای credential احتمالی API تصویر:

```text
/home/radmansi/.config/radman/api-keys/legacy-site.env
```

نسخه فعلی برای تصویر از صفحات عمومی، search و sitemap استفاده می‌کند و محتوای این فایل را نمی‌خواند یا log نمی‌کند. credential نباید در repository قرار گیرد. در صورت استفاده آینده، فایل باید mode `600` داشته باشد.

## پیش‌نیاز

```bash
python3 --version            # 3.11+
python3 -c 'import openpyxl; print(openpyxl.__version__)'  # 3.1.5 روی میزبان
```

در صورت نبود dependency، runner با پیام فارسی و بدون import متوقف می‌شود.

## حالت‌های runner

### inspect — فقط ساختار و انتخاب

```bash
bash scripts/run_excel_import.sh --inspect
```

### plan — نمونه ۲۰ محصول، بدون WordPress

```bash
MAX_PRODUCTS=20 bash scripts/run_excel_import.sh --plan
```

این فرمان Excel را می‌خواند، eligibility/SKU/pricing/category را محاسبه، ۲۰ ردیف نخست pricing preview را روی stdout چاپ و CSV/TXT/manifest خصوصی تولید می‌کند. هیچ web request یا WordPress write ندارد.

### fetch-images — دانلود gallery برای انتخاب فعلی

```bash
MAX_PRODUCTS=20 bash scripts/run_excel_import.sh --fetch-images
```

روش discovery به‌ترتیب:

1. URLهای مستقیم `/product/{id}/`، `/p/{id}/` و `?product_id={id}`؛
2. search سایت با ID و انتخاب لینک منطبق؛
3. sitemap cache که فقط یک‌بار در run ساخته می‌شود.

robots.txt، حداقل فاصله دو ثانیه، User-Agent سفارشی و percent-encoding URL فارسی اعمال می‌شوند. داده محصول از HTML خوانده نمی‌شود؛ parser فقط URLهای تصویر gallery را استخراج می‌کند.

### import-drafts — import manifest دارای نتیجه image fetch

```bash
export APP_ENV=staging
export WP_URL=https://staging.radmansilver.ir
export WP_PATH=/home/radmansi/staging.radmansilver.ir
export CONFIRM_STAGING_APPLY=YES
export RADMAN_PRIVATE_DIR=/home/radmansi/private

bash scripts/run_excel_import.sh --import-drafts \
  --manifest /home/radmansi/private/legacy-cache/runs/excel-import-TIMESTAMP/prepared-products.json
```

runner قبل از اجرای Python یک backup دیتابیس خصوصی می‌سازد. manifest صرفاً plan با `image_status=NOT_FETCHED` قابل import نیست؛ ابتدا باید `--fetch-images` اجرا شود. محصولی که پس از تمام strategyها تصویر ندارد، `image_status=MISSING` می‌گیرد ولی همچنان Draft ساخته می‌شود.

### full-pilot — هزار محصول

```bash
export APP_ENV=staging
export WP_URL=https://staging.radmansilver.ir
export WP_PATH=/home/radmansi/staging.radmansilver.ir
export CONFIRM_STAGING_APPLY=YES
export RADMAN_PRIVATE_DIR=/home/radmansi/private

MAX_PRODUCTS=1000 bash scripts/run_excel_import.sh --full-pilot
```

این مرحله به‌دلیل delay و تعداد galleryها طولانی و پرحجم است. اجرای مرحله‌ای و بازبینی plan قبل از هزار محصول توصیه می‌شود.

## استخراج SKU

1. regex عنوان: `کد\s*([0-9۰-۹]{2,8})`؛
2. در نبود آن، ستون ۲۷ فقط اگر integer بدون نقطه و کمتر از `100000` باشد؛
3. در غیر این صورت `NM-<legacy_id>`.

ارقام فارسی/عربی به لاتین تبدیل می‌شوند. مقدار خام ستون ۲۷ همیشه در `legacy_raw_code` و ID در `legacy_product_id` نگهداری می‌شود. conflict SKU در WordPress skip/report است و محصول موجود overwrite نمی‌شود.

## قیمت‌گذاری تومانی

همه قیمت‌ها تومان‌اند؛ تبدیل ×۱۰ یا ÷۱۰ ممنوع است. محاسبه با `Decimal` انجام می‌شود.

| شواهد عنوان | نرخ تومان/گرم |
|---|---:|
| «درشت»/«بزرگ» نزدیک «نگین»/«عقیق» | 590000 |
| سایر، بدون نگین یا نامطمئن | 650000 |

```text
اگر وزن موجود:
  computed = weight × rate
  selected = max(COL9, computed)
اگر وزن خالی:
  selected = COL9
final = ceil(selected / 50000) × 50000
```

`price_source` یکی از `EXCEL_ONLY`، `MAX_EXCEL` یا `MAX_CALCULATED` است. اگر ستون ۱۰ بزرگ‌تر از final باشد، regular price برابر ستون ۱۰ و sale price برابر final است؛ وگرنه regular برابر final و sale خالی است.

## دسته، موجودی و وضعیت

- شامل «انگشتر» → `rings`؛
- شامل «گردنبند» یا «مدال» → `necklaces`؛
- شامل «دستبند» → `bracelets`؛
- ناشناخته → `rings` همراه review flag.

محصول جدید همیشه Simple و `Draft` است. موجودی واقعی ستون ۱۱ ذخیره می‌شود، `manage_stock=yes` و `backorders=no` است. `legacy_product_id` موجود باعث skip idempotent و SKU موجود باعث skip conflict می‌شود؛ هیچ update روی محصول مالک انجام نمی‌شود.

## سیاست تصویر اصلی

- archive بایت اصلی: `legacy-cache/original-images/<legacy_id>/`؛
- EXIF orientation و resize بدون crop تا max edge 1600؛
- WebP quality 90؛
- بدون تغییر hue/saturation، geometry، background یا زاویه؛
- مدل‌های حذف پس‌زمینه و تولید تصویر در این pipeline فراخوانی نمی‌شوند؛
- failure رنگ/detail → فایل اصلی انتخاب می‌شود؛
- تصویر اول featured و بقیه gallery با ترتیب source هستند.

## گزارش‌ها

```text
RADMAN_PRIVATE_DIR/legacy-cache/runs/excel-import-<timestamp>/
├── prepared-products.json
├── image-discovery-log.json       # پس از fetch
├── import-actions.json            # پس از import
├── image-qa/
├── excel-import-<timestamp>.csv
└── excel-import-<timestamp>-fa.txt
```

هر ردیف گزارش شامل ID، SKU/source، عنوان، دسته، وزن، قیمت Excel/computed/final، price source، stone class، stock، تصویر، action و review flags است.

## failure و rollback

- guard محیط، currency غیر IRT، backup خالی، Excel/dependency نامعتبر و manifest ناامن قبل از import متوقف می‌شوند.
- image missing batch را متوقف نمی‌کند.
- media failure بعد از create محصول را Draft نگه می‌دارد؛ اجرای دوباره به‌علت `legacy_product_id` آن را overwrite نمی‌کند.
- `import-actions.json` شناسه Draftهای ساخته‌شده را برای بازبینی/rollback مالک ثبت می‌کند.
- production، `public_html`، payment، SMS و سرویس‌های نامرتبط خارج از دامنه‌اند.

## وضعیت اجرا

ابزار و تست fixture در repository آماده‌اند. فایل Excel و legacy site از workspace agent قابل دسترسی نبودند؛ هیچ fetch زنده، WordPress write یا import واقعی در این PR انجام نشده است.
