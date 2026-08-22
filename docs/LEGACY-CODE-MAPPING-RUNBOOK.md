# راهنمای نگاشت کد قدیمی به SKU

**بازبینی:** `2026-08-21, Asia/Tehran`
**کتابخانه مشترک:** `agents/lib/legacy_identity.py`

## اولویت استخراج

1. عبارت visible «شناسه کالا»؛
2. `کد`/`code` در عنوان؛
3. `کد`/`code` در متن visible صفحه.

`legacy_id` عدد داخل URL `/product/<legacy_id>/` است و با کد تجاری محصول یکی نیست. هر دو همراه URL دقیق نگهداری می‌شوند.

## نگاشت SKU

| وضعیت کد | رفتار |
|---|---|
| ASCII امن با الگوی `[A-Za-z0-9][A-Za-z0-9._-]*` و طول حداکثر ۱۰۰ | همان کد **دقیقاً** SKU می‌شود |
| رقم فارسی/عربی یا نویسه قابل normalize | فقط همان نویسه‌ها به فرم امن قطعی تبدیل می‌شوند؛ raw code حفظ می‌شود |
| کد Unicode/دارای separator نامعتبر | `LEGACY-<ascii-part>-<SHA256-prefix>` به‌شکل deterministic ساخته می‌شود |
| کد خالی | محصول import نمی‌شود و review می‌گیرد |

فیلدهای `legacy_code_raw` و `radman_legacy_code_raw` همیشه مقدار دیده‌شده را نگه می‌دارند. `legacy_code` نسخه normalize‌شده قابل مقایسه و `sku_mapping_reason` دلیل نگاشت را ثبت می‌کند.

## duplicate و conflict

- duplicate code در batch با مقایسه case-insensitive پس از normalize تشخیص داده و skip/report می‌شود؛
- برخورد دو کد با یک SKU normalize‌شده نیز skip/report می‌شود؛
- پیش از WordPress mutation، همه SKUها بررسی می‌شوند؛ وجود SKU روی هر محصول، کل batch را متوقف می‌کند؛
- وجود `radman_legacy_id`، `legacy_id` یا alias قدیمی `_legacy_store_id` در WooCommerce باعث `SKIP_EXISTING_LEGACY_ID` می‌شود؛ هیچ update انجام نمی‌شود.

## metadata هویتی الزامی

```text
legacy_id
legacy_code
legacy_url
_legacy_store_id
_legacy_product_code
_legacy_product_url
radman_legacy_id
radman_legacy_code
radman_legacy_code_raw
radman_legacy_url
radman_import_source=original_legacy_pipeline
radman_import_version=PR-25
```

## نمونه

```text
AB-12.7  -> AB-12.7             (exact)
۱۲۳۴     -> 1234                (digit normalization; raw=۱۲۳۴)
کد ویژه  -> LEGACY-<hash>       (deterministic safe mapping)
```

هیچ شناسه تصادفی ساخته نمی‌شود. هر تغییر دستی mapping باید پیش از import توسط مالک ثبت و تأیید شود.

## PR-30A — عنوان عمومی بدون کد، هویت private کامل

مسیر Excel جاری از `agents/lib/product_identity.py` استفاده می‌کند. suffix صریح کد فقط در انتهای عنوان پاک می‌شود؛ SKU تغییر نمی‌کند. عنوان کامل اولیه در `legacy_original_title` و mapping قطعی در `legacy_identity_key=<legacy_product_id>:<SKU>` نگهداری می‌شود. کد مدل در specification مشتری نمایش داده می‌شود، نه در `post_title`.

اگر title code با SKU محصول Draft موجود اختلاف داشته باشد، `--enrich-existing` SKU را حفظ و `SKU_TITLE_MISMATCH` ثبت می‌کند. WooCommerce Admin جست‌وجوی استاندارد SKU را پشتیبانی می‌کند؛ گزارش `--identity-report` نیز WP ID، عنوان، SKU، legacy ID/raw code/URL/key و review را بدون mutation خروجی می‌دهد.
