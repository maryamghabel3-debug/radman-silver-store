# راهنمای فارسی import محصولات روی staging

> این ابزار فقط staging را تغییر می‌دهد. محصول جدید همیشه `Draft` است و هیچ پرداخت، پیامک، صفحه حقوقی یا تنظیم production را تغییر نمی‌دهد.

## ۱. آماده‌سازی فایل CSV

1. فایل نمونه را از ریپو باز کنید:
   ```text
   templates/product-import-sample.csv
   ```
2. یک کپی با نام `products.csv` بسازید.
3. هر سه ردیف SAMPLE را حذف یا کامل جایگزین کنید.
4. برای هر محصول:
   - SKU یکتا و مطابق دسته وارد کنید؛
   - وزن خالص نقره را فقط در صورت اطمینان وارد کنید؛
   - mode قیمت را تعیین کنید؛
   - قیمت‌های legacy/manual را مستقیم به **تومان** وارد کنید؛
   - موجودی واقعی را وارد کنید (`1` کاملاً عادی و قابل فروش است)؛
   - توضیحات را مخصوص همان محصول بنویسید.
5. فایل را با UTF-8 CSV ذخیره کنید.

قرارداد کامل ستون‌ها: [PRODUCT-IMPORT-SCHEMA.md](PRODUCT-IMPORT-SCHEMA.md)

## ۲. آپلود با cPanel

در cPanel → File Manager این ساختار را خارج از web root بسازید:

```text
/home/radmansi/.config/radman/import/products.csv
/home/radmansi/.config/radman/import/images/
```

دسترسی پیشنهادی:

```bash
chmod 700 /home/radmansi/.config/radman/import
chmod 700 /home/radmansi/.config/radman/import/images
chmod 600 /home/radmansi/.config/radman/import/products.csv
```

### تصاویر

- فقط تصویرهایی را آپلود کنید که مالک آن‌ها هستید یا مجوز استفاده دارید.
- نام فایل باید دقیقاً با مقدار `image_filenames` برابر باشد.
- چند تصویر با `|` جدا می‌شوند؛ مثال:
  ```text
  RAD-RNG-M-1045-front.jpg|RAD-RNG-M-1045-side.jpg
  ```
- فرمت مجاز: JPG، JPEG، PNG، WebP.
- importer هیچ تصویر یا متن دارای حق نشر را از سایت قدیمی دانلود نمی‌کند.
- اگر فایلی موجود نباشد، warning ثبت می‌شود و import محصول بدون آن فایل ادامه می‌یابد.

## ۳. نرخ روز نقره

برای modeهای وزن‌محور، فایل زیر باید فقط یک عدد صحیح مثبت (تومان/گرم) داشته باشد:

```text
/home/radmansi/.config/radman/state/daily_rate.txt
```

مثال قالب (عدد واقعی را مالک وارد می‌کند):

```text
85000
```

## ۴. مرحله الزامی Plan

ابتدا ZIP آخر `main` را از GitHub دانلود، در cPanel آپلود و در مسیر زیر extract کنید:

```text
/home/radmansi/radman-deploy/repo
```

سپس این دستور read-only را اجرا کنید:

```bash
export PATH="$HOME/bin:$PATH"; APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman bash /home/radmansi/radman-deploy/repo/scripts/import_products.sh --plan
```

خروجی plan برای هر ردیف نشان می‌دهد:

- SKU و شماره ردیف؛
- `CREATE` یا `UPDATE` (اگر WP قابل inspection باشد)؛
- دسته و pricing mode؛
- stock و قیمت محاسبه‌شده؛
- تعداد تصاویر موجود.

اگر `CHECK-AT-APPLY` نمایش داده شد یعنی plan محلی به WP دسترسی نداشته، اما هیچ mutation انجام نشده است. روی host معمولاً نتیجه CREATE/UPDATE نمایش داده می‌شود.

## ۵. Apply روی staging

فقط پس از بازبینی کامل plan، **یک دستور زیر** را اجرا کنید:

```bash
export PATH="$HOME/bin:$PATH"; APP_ENV=staging CONFIRM_STAGING_APPLY=YES WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman bash /home/radmansi/radman-deploy/repo/scripts/import_products.sh --apply-staging
```

قبل از هر mutation این دو backup ساخته می‌شوند:

```text
~/.config/radman/backups/pre-product-import-<timestamp>.sql
~/.config/radman/backups/product-import-input-<timestamp>.csv
```

اگر backup دیتابیس خالی یا ناموفق باشد، import متوقف می‌شود.

## ۶. بازبینی Draftها در WooCommerce

1. وارد `staging.radmansilver.ir/wp-admin` شوید.
2. مسیر Products → All Products را باز کنید.
3. محصولات Draft جدید را بر اساس SKU پیدا کنید.
4. برای هر محصول این موارد را بازبینی کنید:
   - عنوان و توضیحات؛
   - دسته اصلی؛
   - قیمت تومان؛
   - وزن، عیار و نوع/ارزش سنگ؛
   - stock دقیق؛
   - تصویر featured و gallery؛
   - نمایش موبایل و دسکتاپ.
5. **انتشار دستی یک تصمیم جداگانه مالک است. importer هیچ محصولی را publish نمی‌کند.**

وضعیت محصول موجود با اجرای مجدد CSV حفظ می‌شود؛ بنابراین rerun یک محصول قبلاً منتشرشده را خودکار Draft یا Publish نمی‌کند.

## ۷. رفع خطاهای رایج

| خطا | راه‌حل |
|---|---|
| `SAMPLE row detected` | پیشوند SAMPLE و متن نمونه را با داده واقعی جایگزین کنید |
| `daily rate file is missing` | فایل `state/daily_rate.txt` را با یک عدد تومان/گرم بسازید |
| `SKU category code does not match` | RNG↔rings، NEC↔necklaces، BRC↔bracelets را اصلاح کنید |
| `image missing, skipped` | filename و حروف بزرگ/کوچک را با فایل cPanel تطبیق دهید |
| `product category not found` | وجود categories مصوب staging را بررسی کنید |
| `Existing SKU is not a simple product` | محصول variable/نوع دیگر را دستی بررسی کنید؛ importer آن را overwrite نمی‌کند |
| `blog_public` یا currency guard | staging باید `blog_public=0` و currency=`IRT` باشد |
| lock held | صبر کنید اجرای قبلی تمام شود؛ بدون اطمینان lock را حذف نکنید |

## ۸. Rollback

در صورت خطا:

1. import بعدی را متوقف کنید؛
2. فهرست SKUهای همان CSV را ثبت کنید؛
3. محصولات Draft ایجادشده را در admin بررسی کنید؛
4. در صورت نیاز، backup SQL را فقط با هماهنگی فنی restore کنید؛
5. فایل backup CSV را برای audit نگه دارید.

## ۹. محدودیت‌های قطعی

- production/public_html پشتیبانی نمی‌شود.
- محصول جدید فقط Draft است.
- هیچ payment gateway یا SMS فعال نمی‌شود.
- هیچ legal page منتشر نمی‌شود.
- هیچ تصویر remote دانلود نمی‌شود.
- داده عمومی legacy بدون تأیید مالک «حقیقت نهایی» فرض نمی‌شود.
