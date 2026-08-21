# راهنمای اجرای خط لوله محصولات واقعی با تصویر اصلی

**نسخه:** PR-25
**بازبینی سیاست و نرخ موقت:** `2026-08-21, Asia/Tehran`
**محیط مجاز:** فقط `https://staging.radmansilver.ir` در `/home/radmansi/staging.radmansilver.ir`

این خط لوله حداکثر ۱۰ محصول واقعی را مستقیماً از صفحات عمومی `noghrehmashhad.ir` دریافت می‌کند؛ مالک لازم نیست CSV یا Google Sheet بسازد. تصاویر اصلی، داده استخراج‌شده، گزارش‌ها و نسخه پشتیبان دیتابیس فقط زیر `RADMAN_PRIVATE_DIR` نگهداری می‌شوند.

## ضمانت‌های قطعی

- قیمت قدیمی **تومان** است؛ تبدیل ریال/تومان مطلقاً انجام نمی‌شود.
- محصول جدید فقط `Draft`، با موجودی `1` و `backorders=no` ساخته می‌شود.
- محصولی که `legacy_id` آن از قبل وجود دارد، بدون تغییر رد می‌شود.
- تعارض SKU کل batch را **قبل از هر mutation** متوقف می‌کند.
- محصول موجود یا ویرایش‌شده توسط مالک هرگز overwrite نمی‌شود.
- برای import، QA تصویر الزامی است. خروجی مردود با فایل اصلی دست‌نخورده جایگزین می‌شود.
- `public_html`، Production، پرداخت، SMS، Telegram و سرویس‌های نامرتبط خارج از محدوده‌اند.

## پیش‌نیاز میزبان

- Python 3.11+ با Pillow (محاسبات QA بدون NumPy انجام می‌شوند)؛
- WP-CLI و WooCommerce در Staging؛
- `RADMAN_PRIVATE_DIR` خصوصی و خارج از web root؛
- اجرای دستور از checkout همین repository روی میزبان ایرانی.

## فرمان‌ها

همه حالت‌ها از یک runner اجرا می‌شوند:

```sh
cd /path/to/radman-silver-store
scripts/run_original_product_import.sh --plan
```

### ۱. فقط scrape خودکار

```sh
RADMAN_PRIVATE_DIR=/home/radmansi/private \
  scripts/run_original_product_import.sh --scrape-only --limit 10
```

این مرحله robots.txt و فاصله حداقل دو ثانیه را رعایت می‌کند و WordPress را تغییر نمی‌دهد.

### ۲. QA تصویر و آماده‌سازی manifest

```sh
RADMAN_PRIVATE_DIR=/home/radmansi/private \
  scripts/run_original_product_import.sh --image-qa
```

آخرین `scrape.json` انتخاب می‌شود. برای انتخاب صریح:

```sh
scripts/run_original_product_import.sh --image-qa \
  --source-manifest /home/radmansi/private/legacy-cache/runs/TIMESTAMP/scrape.json
```

### ۳. پیش‌نمایش قیمت بدون import

```sh
scripts/run_original_product_import.sh --pricing-preview
```

این حالت classifier و قیمت‌گذاری را اجرا می‌کند اما QA/import را مجاز نمی‌کند.

### ۴. import پیش‌نویس‌های آماده

ابتدا manifest حاصل از `--image-qa` را **دستی بازبینی** کنید. سپس:

```sh
export APP_ENV=staging
export WP_URL=https://staging.radmansilver.ir
export WP_PATH=/home/radmansi/staging.radmansilver.ir
export CONFIRM_STAGING_APPLY=YES
export RADMAN_PRIVATE_DIR=/home/radmansi/private

scripts/run_original_product_import.sh --import-drafts \
  --prepared-manifest /home/radmansi/private/legacy-cache/runs/TIMESTAMP/prepared-products.json
```

runner پیش از import یک `wp db export` تازه در `RADMAN_PRIVATE_DIR/backups/` می‌سازد. Python وجود، غیرخالی بودن، پسوند SQL و تازگی حداکثر شش‌ساعته backup را دوباره بررسی می‌کند.

### ۵. پایلوت کامل

```sh
# همان چهار متغیر guard بالا باید تنظیم باشند.
scripts/run_original_product_import.sh --full-pilot --limit 10
```

این حالت scrape، QA، classifier، pricing، report و create-only draft import را پشت‌سرهم انجام می‌دهد. برای کنترل بیشتر، اجرای مرحله‌ای توصیه می‌شود.

## خروجی‌ها

```text
RADMAN_PRIVATE_DIR/legacy-cache/
├── original-products/<legacy_id>.json
├── original-images/<legacy_id>/<position>-original.<ext>
├── processed-images/<legacy_id>/<position>.webp
└── runs/<timestamp>/
    ├── scrape.json
    ├── prepared-products.json
    ├── import-actions.json                 # فقط پس از import
    ├── image-qa/*-before-after.jpg
    ├── original-products-<timestamp>.csv
    └── original-products-<timestamp>-fa.txt
```

CSV صرفاً **گزارش تولیدشده خودکار** است و source دستی import نیست. گزارش شامل قیمت، کلاس نگین، سلامت تصویر، duplicate/identity/SKU conflict، موارد ردشده در scrape، review و import action است.

## توقف و بازگشت

- اگر conflict، داده نامعتبر، guard محیط، currency غیر `IRT`، backup، یا فایل رسانه مشکل داشته باشد، import متوقف می‌شود.
- در failure رسانه بعد از ساخت محصول، محصول همچنان Draft می‌ماند؛ آن را دستی بررسی کنید. اجرای دوباره به‌علت `legacy_id` موجود آن را overwrite نمی‌کند.
- rollback خودکار انجام نمی‌شود. از `import-actions.json` برای شناسایی Draftهای ساخته‌شده استفاده کنید و فقط پس از تأیید مالک آن‌ها را حذف کنید؛ در صورت نیاز دیتابیس را از backup همان اجرا برگردانید.

## وضعیت واقعی

این repository ابزار و تست آفلاین را فراهم می‌کند. اجرای scrape زنده و mutation میزبان باید توسط مالک روی MizbanFa داخل ایران انجام شود؛ این سند هیچ اجرای زنده یا import انجام‌شده‌ای را ادعا نمی‌کند.
