# PR-32 — استخراج دقیق و بدون آلودگی مشخصات HTML

## سیاست قطعی

API سایت قدیمی همچنان **DEFERRED** است. `--enrich-existing` نتیجه SKU search را فقط وقتی می‌پذیرد که حداقل یکی از این شواهد برقرار باشد: SKU/code دقیق، legacy product ID دقیق، یا overlap توکن‌های title حداقل 60 درصد. حالت title-only با `LOW_CONFIDENCE` گزارش می‌شود. نبود شاهد معتبر، `IDENTITY_MISMATCH` است و محصول موجود اصلاً update نمی‌شود.

مشخصات فقط از container اصلی attributes/specifications خوانده می‌شوند. related/suggested/recent products، comments، sidebar/category widgets و block دارای کد محصول دیگر حذف می‌شوند. مقدارهای غیرمنطقی مانند `های اصلی`، عبارت‌های طولانی محصول، setting آلوده و engraving دارای کد دیگر drop می‌شوند.

سنگ و رنگ با title Draft cross-check می‌شوند. برای نمونه title «عقیق سرخ» هرگز نباید رنگ «آبی» بگیرد؛ در conflict، `COLOR_MISMATCH` ثبت و رنگ title ترجیح داده می‌شود.

## فرمان دقیق مالک برای ۲۰ Draft موجود

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
CONFIRM_STAGING_APPLY=YES \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --enrich-existing
```

runner پیش از update backup خصوصی می‌سازد. هیچ محصولی create/publish نمی‌شود. image/gallery، title، SKU، status، stock و category دست‌نخورده می‌مانند. rerun مشخصات اشتباه قبلی را با fieldهای validated overwrite می‌کند؛ اگر کمتر از سه field معتبر بماند، description حداقلی امن جایگزین می‌شود. `_sale_price` حذف و کاهش قیمت ممنوع است.

## گزارش کیفیت هر محصول

CSV/TXT/JSON خصوصی شامل این فیلدهاست:

- `match_status`: `MATCHED`, `LOW_CONFIDENCE`, `IDENTITY_MISMATCH`
- `fields_extracted`
- `fields_validated`
- `dropped_fields` همراه reason
- `color_mismatch`
- `stone_source`: `TABLE`, `TITLE`, `DROPPED`

## سه نمونه اصلاح‌شده

### ۱. عقیق سرخ — رنگ آبی حذف شده

```text
انگشتر عقیق سرخ

مشخصات فنی ثبت‌شده برای این قطعه از مجموعه رادمان سیلور:

- وزن: 8 گرم
- نوع سنگ: عقیق
- رنگ نگین: سرخ
- عیار نقره: 925
- کد مدل: 1057

اطلاعات فوق فقط از مشخصات فنی صفحه همان محصول استخراج شده است.
```

### ۲. در نجف

```text
گردنبند نقره در نجف

مشخصات فنی ثبت‌شده برای این قطعه از مجموعه رادمان سیلور:

- وزن: 12 گرم
- نوع سنگ: در نجف
- رنگ نگین: سفید
- عیار نقره: 925
- ابعاد نگین: 18 × 12 میلی متر
- کد مدل: 1014

اطلاعات فوق فقط از مشخصات فنی صفحه همان محصول استخراج شده است.
```

### ۳. فقط دو field معتبر

```text
انگشتر نقره ساده

این محصول از مجموعه رادمان سیلور با کد مدل 1057 در حال تکمیل مشخصات فنی است. اطلاعات تکمیلی پیش از انتشار نهایی بازبینی می‌شود.
```

حالت سوم `INSUFFICIENT_SPECS` می‌گیرد و هیچ مقدار garbage نمایش داده نمی‌شود.
