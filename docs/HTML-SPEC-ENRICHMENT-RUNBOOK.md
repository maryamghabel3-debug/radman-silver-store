# PR-31 — تعمیر مشخصات Draftها از صفحه HTML محصول

## تصمیم منبع

API سایت قدیمی در این مرحله **DEFERRED** است. `--enrich-existing` ابتدا برای SKU در `https://noghrehmashhad.ir/?s=<SKU>` جست‌وجو می‌کند، بهترین URL/title را امتیاز می‌دهد و سپس فقط صفحه واقعی محصول را fetch می‌کند. Excel منبع selection، price، stock و active flag باقی می‌ماند.

فقط weight، stone type/color، setting type، silver purity، dimensions، size، engraving و model code پذیرفته می‌شوند. phone/contact/address، shipping/payment، warranty/support/return، SEO و متن بازاریابی وارد محتوا یا meta نمی‌شوند. `نمایش بیشتر/کمتر` حذف می‌شود.

## فرمان دقیق مالک برای ۲۰ Draft موجود

```bash
APP_ENV=staging \
WP_URL=https://staging.radmansilver.ir \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
CONFIRM_STAGING_APPLY=YES \
RADMAN_PRIVATE_DIR=/home/radmansi/private \
EXCEL_FILE=/home/radmansi/radman-deploy/products_20260821_182238.xlsx \
MAX_PRODUCTS=20 \
bash scripts/run_excel_import.sh --enrich-existing
```

runner پیش از update یک database backup خصوصی می‌سازد. mode فقط Draftهای موجود دارای `legacy_product_id` را update می‌کند؛ هیچ محصولی create/publish نمی‌شود. image/gallery، SKU، status، stock و category دست‌نخورده می‌مانند. فقط content، excerpt، technical meta و در صورت بالاتر بودن کف محاسبه‌شده از current price، قیمت به‌روزرسانی می‌شود. `_sale_price` همیشه حذف می‌شود.

## سه نمونه خروجی

### ۱. هشت field فنی

```text
انگشتر عقیق سیاه

مشخصات فنی ثبت‌شده برای این قطعه از مجموعه رادمان سیلور:

- وزن: 8.2 گرم
- نوع سنگ: عقیق
- رنگ نگین: سیاه
- نوع رکاب: دست ساز
- عیار نقره: 925
- ابعاد نگین: 14 × 10 میلی متر
- سایز: 60
- کد مدل: 1057

اطلاعات فوق فقط از مشخصات فنی صفحه همان محصول استخراج شده است.
```

### ۲. پنج field فنی

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

### ۳. کمتر از سه field

```text
دستبند نقره

این محصول از مجموعه رادمان سیلور با کد مدل 1060 در حال تکمیل مشخصات فنی است. اطلاعات تکمیلی پیش از انتشار نهایی بازبینی می‌شود.
```

این حالت `INSUFFICIENT_SPECS` و review می‌گیرد.
