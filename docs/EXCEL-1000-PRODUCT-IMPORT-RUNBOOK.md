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

### enrich-existing — اصلاح Draftهای موجود با مشخصات واقعی

این mode فقط Draftهای دارای meta `legacy_product_id` را با Excel تطبیق می‌دهد، همان صفحه ID-based را یک‌بار fetch می‌کند، specificationها و توضیح یکتا را می‌سازد و post content/meta را idempotent به‌روزرسانی می‌کند. stock، category و image دست‌نخورده می‌مانند. قیمت فقط وقتی تغییر می‌کند که وزن Excel خالی و وزن live قابل‌استفاده باشد و محاسبه جدید final را تغییر دهد.

```bash
export APP_ENV=staging
export WP_URL=https://staging.radmansilver.ir
export WP_PATH=/home/radmansi/staging.radmansilver.ir
export CONFIRM_STAGING_APPLY=YES
export RADMAN_PRIVATE_DIR=/home/radmansi/private

MAX_PRODUCTS=20 bash scripts/run_excel_import.sh --enrich-existing
```

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

`price_source` یکی از `EXCEL_ONLY`، `MAX_EXCEL` یا `MAX_CALCULATED` است. طبق سیاست لوکس HOTFIX، ستون ۱۰ فقط برای trace نگهداری و در storefront نادیده گرفته می‌شود: `regular_price` همیشه دقیقاً برابر `final` است، هیچ sale price ساخته نمی‌شود و نمایش خط‌خورده مجاز نیست.

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

## مشخصات واقعی و توضیح یکتا (PR-29)

همان HTTP response که برای gallery استفاده می‌شود، بخش «مشخصات» را نیز parse می‌کند؛ round-trip دوم انجام نمی‌شود. pairهای `label:value` با جداکننده `·` مستقل از ترتیب/تعداد خوانده می‌شوند. labelهای شناخته‌شده دسته‌بندی، وزن، نوع رکاب، رنگ نگین، نوع سنگ، نوع حکاکی، عیار نقره و سایز هستند؛ label ناشناخته نیز در JSON حفظ و در گزارش batch فهرست می‌شود.

متادیتا:

```text
radman_legacy_specs
radman_spec_stone_type
radman_spec_stone_color
radman_spec_band_type
radman_spec_engraving_type
radman_spec_silver_purity
radman_spec_size
radman_spec_weight_grams
radman_spec_weight_display
weight_source
description_source
radman_requires_review
```

اگر وزن Excel خالی و وزن live معتبر باشد، `weight_source=LIVE_PAGE` و قیمت دوباره با نرخ PR-28 محاسبه می‌شود. اگر وزن Excel موجود باشد، `weight_source=EXCEL` باقی می‌ماند؛ اختلاف بیش از `0.5g` فقط `WEIGHT_MISMATCH` و review ایجاد می‌کند.

وقتی مشخصات وجود دارد، description قابل‌مشاهده از title، category، سنگ/رنگ، رکاب، وزن، حکاکی، سایز، labelهای اضافی و کد مدل ساخته می‌شود (`SPECS_TEMPLATE`). متن عمومی COL 29 در این حالت استفاده نمی‌شود. فقط در نبود کامل spec، COL 29/COL 28 به‌صورت `SEO_FALLBACK` مجاز است. اجرای `--full-pilot` برای batchهای 100/1000 این enrichment را به‌طور پیش‌فرض انجام می‌دهد.

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

هر ردیف گزارش شامل ID، SKU/source، عنوان، دسته، وزن، قیمت Excel/computed/final، price source، stone class، stone type/color، band type، purity، spec weight، weight/description source، labelهای ناشناخته، stock، تصویر، action و review flags است. TXT همچنین فراوانی همه labelهای ناشناخته batch را جمع‌بندی می‌کند.

## failure و rollback

- guard محیط، currency غیر IRT، backup خالی، Excel/dependency نامعتبر و manifest ناامن قبل از import متوقف می‌شوند.
- image missing batch را متوقف نمی‌کند.
- media failure بعد از create محصول را Draft نگه می‌دارد؛ اجرای دوباره به‌علت `legacy_product_id` آن را overwrite نمی‌کند.
- `import-actions.json` شناسه Draftهای ساخته‌شده را برای بازبینی/rollback مالک ثبت می‌کند.
- production، `public_html`، payment، SMS و سرویس‌های نامرتبط خارج از دامنه‌اند.

## وضعیت اجرا

ابزار و تست fixture در repository آماده‌اند. فایل Excel و legacy site از workspace agent قابل دسترسی نبودند؛ هیچ fetch زنده، WordPress write یا import واقعی در این PR انجام نشده است.
