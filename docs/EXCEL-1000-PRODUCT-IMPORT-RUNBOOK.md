# راهنمای import هزار محصول جدیدتر از Excel با تصاویر اصلی

**نسخه:** PR-33 (clean public descriptions + strict HTML validation)

**تصمیم قطعی منبع داده:** Excel منبع selection، price، stock و active flag است. API سایت قدیمی deferred است. برای `--enrich-existing`، صفحه HTML واقعی محصول پس از SKU search منبع اصلی مشخصات فنی allowlisted است؛ متن عمومی/SEO و contact وارد رادمان نمی‌شود.

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

## API deferred

API autodiscovery در این مرحله موفق نبود و هیچ `--api-probe` یا credential API در runner استفاده نمی‌شود. مسیر رسمی PR-32، SKU search و fetch صفحه HTML واقعی محصول است.

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

این mode فقط Draftهای دارای meta `legacy_product_id` را با Excel تطبیق می‌دهد. ابتدا `/?s=<SKU>` را می‌خواند، بهترین نتیجه مطابق SKU/title را انتخاب می‌کند و سپس صفحه واقعی محصول را fetch می‌کند. table، definition list، div/span و visible labeled blocks—including بخش «نمایش بیشتر/کمتر»—با allowlist سخت استخراج می‌شوند. محصول recreate نمی‌شود و title، SKU، stock، category، featured image، gallery و Draft status دست‌نخورده می‌مانند. فقط content، excerpt و technical meta نوشته می‌شوند؛ قیمت فقط وقتی بالا می‌رود که وزن live مجاز کف بالاتری از current بسازد. sale price حذف می‌شود.

```bash
export APP_ENV=staging
export WP_URL=https://staging.radmansilver.ir
export WP_PATH=/home/radmansi/staging.radmansilver.ir
export CONFIRM_STAGING_APPLY=YES
export RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman

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

## عنوان عمومی لوکس و هویت legacy (PR-30A)

suffix صریح انتهای عنوان مانند `کد 1058`، `کد مدل 1007`، `کد محصول 1008` یا `شناسه کالا 1057` از `post_title` حذف می‌شود. اعداد معنادار بدون label، از جمله `عیار 925` و `طرح 12 پر`، حذف نمی‌شوند. کد normalize‌شده همچنان SKU و ردیف قابل‌مشاهده «کد مدل» در مشخصات است.

متادیتای private زیر mapping کامل را حفظ می‌کند:

```text
legacy_product_id
radman_legacy_code
legacy_raw_code
legacy_original_title
legacy_url
legacy_identity_key
legacy_title_cleanup_status
legacy_title_cleanup_timestamp
```

در `--enrich-existing` محصول Draft موجود با `legacy_product_id` update می‌شود و recreate نمی‌شود. title و SKU فعلی تغییر نمی‌کنند؛ mismatch فقط report/review می‌شود. content، excerpt، technical meta و در صورت floor بالاتر price مجازند؛ featured image، gallery، category، stock و Draft status دست‌نخورده می‌مانند.

گزارش read-only هویت:

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
RADMAN_PRIVATE_DIR=/home/radmansi/private \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --identity-report
```

WooCommerce Admin به‌طور استاندارد SKU را جست‌وجو می‌کند؛ customization اضافه لازم نیست. agentها می‌توانند با `legacy_product_id`، `legacy_url` یا `legacy_identity_key` reconciliation کنند.

## قیمت‌گذاری تومانی

همه قیمت‌ها تومان‌اند؛ تبدیل ×۱۰ یا ÷۱۰ ممنوع است. محاسبه با `Decimal` انجام می‌شود.

| شواهد عنوان | نرخ تومان/گرم |
|---|---:|
| «درشت»/«بزرگ» نزدیک «نگین»/«عقیق» | 590000 |
| سایر، بدون نگین یا نامطمئن | 650000 |

```text
legacy_price = exact COL9
اگر وزن موجود:
  computed_floor = weight × rate
  selected = max(legacy_price, computed_floor)
اگر وزن خالی:
  selected = legacy_price
final = ceil(selected فقط در صورت اعشاری بودن، تا تومان کامل بعدی)
```

هیچ rounding اجباری 50000 تومانی و هیچ charm/9-ending وجود ندارد. `price_source` یکی از `LEGACY_MIRROR`، `MAX_EXACT_LEGACY` یا `MAX_EXACT_COMPUTED_FLOOR` است. ستون ۱۰ فقط trace است؛ `regular_price == current_price == final_price` و sale price همیشه خالی می‌ماند.

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

## مشخصات دقیق، scoped و توضیح امن (PR-32)

labelهای مجاز: وزن/وزن تقریبی/وزن محصول، نوع سنگ/سنگ/نوع نگین، رنگ نگین/رنگ سنگ/رنگ، نوع رکاب/رکاب، عیار نقره/عیار/نقره، ابعاد/ابعاد نگین/اندازه نگین، سایز/اندازه، کد/کد مدل/شناسه کالا و حکاکی. unknown label و تمام phone/contact/address، shipping/payment، warranty/support/return و SEO/general marketing حذف می‌شوند.

PR-32 ابتدا page identity را با SKU/code، legacy ID یا title overlap حداقل 60٪ تأیید می‌کند؛ سپس فقط container اصلی مشخصات را parse می‌کند. related/suggested/recent products، comments/sidebar/widgets و block دارای کد دیگر کنار گذاشته می‌شوند. stone/color/setting/engraving/weight/purity validation اختصاصی دارند و stone/color با title cross-check می‌شوند. mismatch هویتی بدون هیچ WordPress update گزارش می‌شود.

متادیتای فنی شامل `radman_legacy_specs`, fieldهای `radman_spec_*`, `radman_spec_dimensions`, `radman_spec_model_code`, `radman_spec_status` و `radman_spec_count` است. کمتر از سه field فنی، `MINIMAL_SAFE` و `INSUFFICIENT_SPECS` می‌گیرد. description verified شامل title، intro کوتاه، فقط bulletهای واقعی و `کد مدل` است؛ promise یا scarcity ساختگی ندارد.

اگر وزن Excel خالی و وزن live معتبر باشد، floor قیمت محاسبه می‌شود؛ فقط floor بالاتر از current قابل اعمال است و کاهش قیمت ممنوع است. `_sale_price` حذف و regular/current همگام می‌شوند.

نمونه‌ها و فرمان owner در `docs/HTML-SPEC-ENRICHMENT-RUNBOOK.md` ثبت شده‌اند.

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
