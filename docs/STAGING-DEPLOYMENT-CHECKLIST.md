# چک‌لیست استقرار و پیکربندی محیط آزمایشی (`STAGING-DEPLOYMENT-CHECKLIST.md`)

> **راهنمای اجرایی استقرار وردپرس و ووکامرس در محیط استیجینگ (Staging Setup Checklist)**
> *این چک‌لیست مراحل گام‌به‌گام نصب، مقاوم‌سازی، تست و پیکربندی فروشگاه رادمان سیلور (`radman-silver-store`) را قبل از ورود به سرور پروداکشن پوشش می‌دهد. تمام ادعاهای این چک‌لیست به دو دسته «تأییدشده با evidence» و «PENDING» تقسیم شده‌اند تا اغراق صورت نگیرد.*

> **راهنمای وضعیت‌ها:**
> - **`DONE (verified)`** — روی میزبان واقعاً انجام و تأیید شده است
> - **`PENDING`** — هنوز انجام یا به‌طور کامل تست نشده است
> - **`NOT APPLICABLE`** — غیرقابل اعمال / بلاموضوع

---

## ۱. پیش‌نیازهای دسترسی سرور

- [x] `DONE (verified)` : دسترسی به پنل مدیریت سرور (cPanel `radmansi` روی پلن مارس میزبان‌فا، LiteSpeed).
- [x] `DONE (verified)` : رکوردهای DNS ساب‌دامنهٔ استیجینگ (`staging.radmansilver.ir`) و SSL از نوع Let's Encrypt (`HTTP/2 200`).
- [x] `DONE (verified)` : ایجاد پایگاه داده اختصاصی و کاربر مستقل با دسترسی کامل؛ اتصال موفق بود.

## ۲. محیط PHP / DB / ابزارها

- [x] `DONE (verified)` : PHP `8.2.31`
- [x] `DONE (verified)` : MariaDB `11.4.12-MariaDB`
- [x] `DONE (verified)` : WP-CLI `2.12.0`، Python `3.11.15` در `/opt/alt/python311/bin/python3.11`
- [x] `DONE (verified)` : `wp db check: Success` (یک نکتهٔ اطلاعاتی غیرمسدودکننده روی `wp_wfls_role_counts`)

## ۳. نصب وردپرس و ووکامرس

- [x] `DONE (verified)` : هسته وردپرس `7.0.3` روی `https://staging.radmansilver.ir`
- [x] `DONE (verified)` : تایم‌زون `Asia/Tehran`، زبان `fa_IR`، permalink `/%postname%/`
- [x] `DONE (verified)` : WooCommerce `11.0.1`
- [x] `DONE (verified)` : Persian WooCommerce `10.0.4`
- [x] `DONE (verified)` : گزینه پول `IRT` (تومان) — **فقط برای ذخیره‌سازی دیتابیس، نمایش محصول و نمایش سبد خرید** تأیید شده است (Gate A پاس شده).
- [ ] `PENDING` : دروازهٔ امنیتی ارز، بخش B (Payment/Schema Gate):
  - [ ] مجموع سبد در صفحهٔ checkout
  - [ ] callback درگاه (Gateland/Zarinpal)
  - [ ] خروجی JSON-LD/Schema
  - [ ] خروجی پول در سفارش، فاکتور و ایمیل
- [x] `DONE (verified — placeholder state)` : صفحات استاتیک ۱۱‌گانه با شناسه‌های `21–31` به‌صورت **Draft placeholder** ایجاد شده‌اند (متن موقت bootstrap).
- [ ] `PENDING (full content deployment)` : **ایمپورت محتوای کامل** `content/static-pages/` به صفحات `21–31` از طریق رانر `scripts/radman_stage_apply.sh` (idempotent، پیش‌فرض `--plan`، بدون publish).
- [x] `DONE (verified)` : صفحه اصلی شناسه `18` منتشر و به‌عنوان `static front page` تنظیم شده است.

## ۴. پوسته و قالب فرزند

- [x] `DONE (verified)` : قالب والد Blocksy `2.1.52` و Blocksy Companion `2.1.52`
- [x] `DONE (verified)` : قالب فرزند `blocksy-child v1.0.0` با پالت مصوب (`#0B0B0E` پس‌زمینه، `#FAF7F2` متن) فعال است.
- [x] `DONE (verified)` : فایل‌های `style.css`، `functions.php` و `README.md` در مخزن (`theme/blocksy-child/`) و در استیجینگ وجود دارند.
- [ ] `PENDING` : به‌روزرسانی و تطبیق‌سنجی (diff) child theme از طریق رانر و بک‌آپ خودکار قبل از اعمال.

## ۵. افزونه‌های مصوب (وضعیت نصب/پیکربندی)

- [x] `DONE (verified)` : Gateland `2.4.5` — فقط نصب شده؛ پیکربندی درگاه **PENDING** است.
- [ ] `PENDING` : پیکربندی Gateland/Zarinpal (فقط در استیجینگ/سندباکس تا مأموریت صریح).
- [ ] `PENDING` : Kavenegar SMS — نصب/پیکربندی و تست سندباکس.
- [x] `DONE (verified)` : RankMath SEO `1.0.275` نصب شد؛ اجرای ویزارد **PENDING**.
- [x] `DONE (verified)` : Wordfence `9.0.0` نصب شد؛ سخت‌گیرانه کردن فایروال **PENDING**.
- [x] `DONE (verified)` : UpdraftPlus `1.26.6` نصب شد؛ تنظیم مقصد بک‌آپ ابری **PENDING**.
- [x] `DONE (verified)` : LiteSpeed Cache `7.9` نصب شد؛ تنظیمات پیشرفتهٔ کش **PENDING**.
- [ ] `PENDING HOST REDIS CONFIGURATION` : Redis Object Cache.
- [ ] `PENDING` : اجرای ویزارد راه‌اندازی اولیه ووکامرس.

## ۶. محیط استیجینگ و noindex

- [x] `DONE (verified)` : ساب‌دامنهٔ مستقل `https://staging.radmansilver.ir`، جدا از دامنه اصلی.
- [x] `DONE (verified)` : `blog_public = 0` (noindex) فعال باقی می‌ماند. رانر پیش از اعمال این شرط را بررسی می‌کند و در غیر این صورت abort می‌کند.

## ۷. مدیریت و امنیت

- [x] `DONE (verified)` : ورود به wp-admin با شناسه امن `radmanadmin` توسط مالک؛ رمزها بعد از نصب چرخش شده‌اند.
- [x] `DONE (verified)` : فایل محیطی خصوصی (`/home/radmansi/.config/radman/staging.env`) خارج از وب‌روت با `chmod 600`.
- [ ] `PENDING hardening` : مهاجرت کامل `wp-config.php` به env-loader و حذف رمز دیتابیس از آن.
- [ ] `PENDING` : فعال‌سازی 2FA و قوانین سخت‌گیرانه Wordfence.

## ۸. پاکسازی صفحات پیش‌فرض/تکراری

- [x] `DONE (verified)` : Page ID `2` (Sample Page) حذف شده است.
- [x] `DONE (verified)` : Page ID `3` حذف شده است.
- [ ] `PENDING host verification` : Page ID `10` (با محتوای `refund_returns`) — وضعیت حذف نیاز به بررسی روی میزبان دارد. ادعای حذف آن **ثبت نمی‌شود**.

## ۹. ابزارهای خودکارسازی استیجینگ (reviewed runners)

- [x] `DONE (repo)` : اسکریپت رندر `scripts/render_static_pages.py` (فقط stdlib، بدون وابستگی پایتون).
- [x] `DONE (repo)` : رانر پایین‌لایه `scripts/radman_branding_and_content_import.sh` با قفل `flock`، بک‌آپ پیش از تغییر، و guards سخت‌گیرانه استیجینگ.
- [x] `DONE (repo)` : رانر مالک با یک دستور `scripts/radman_stage_apply.sh` (پیش‌فرض `--plan`، `--apply-staging` فقط با `CONFIRM_STAGING_APPLY=YES`)؛ باگ `/dev/fd` جیل‌شل رفع شده (بدون process substitution، build dir با `mktemp -d`).
- [x] `DONE (repo)` : gate محتوای کامل (بدون placeholder) با `scripts/check_no_placeholders.py` در هر اجرای plan اعمال می‌شود.
- [x] `DONE (repo)` : self-test محلی `scripts/test_plan_runner.sh` اجرای plan، چاپ جدول DEPLOY PLAN و عدم وجود placeholder را تضمین می‌کند.
- [ ] `PENDING host execution` : اجرای `bash scripts/radman_stage_apply.sh --plan` روی میزبان توسط مالک/عامل و بررسی خروجی (پس از آن می‌توان به مرحله apply رفت).
- [ ] `PENDING reviewer approval` : اجرای `--apply-staging` پس از تأیید صریح.

## ۱۰. تست‌های آتی / باقی‌مانده

- [ ] `PENDING` : تست آپلود رسانه و تبدیل WebP.
- [ ] `PENDING` : تست REST API (`/wp-json/wc/v3/products`).
- [ ] `PENDING` : تست Webhook/Telegram notification.
- [ ] `PENDING` : تست مقصد بک‌آپ UpdraftPlus.
- [ ] `PENDING` : استقرار runtime عامل‌های پایتون (`agents/`).
- [ ] `PENDING` : ایمپورت محصولات و فعال‌سازی عامل قیمت‌گذاری.
- [ ] `PENDING` : استقرار پروداکشن (`public_html` دست‌نخورده باقی می‌ماند تا مأموریت صریح).

---

## ۱۱. بیانیه رسمی وضعیت ارز

> *Toman direct input is verified for WooCommerce database storage, product display, and cart display. Payment, checkout, order, email, and Schema currency behavior remain PENDING and must pass before payment activation or production launch.*

## ۱۲. بیانیه رسمی دسترسی عامل

راه دسترسی مصوب به میزبان در سند [HOST-OPS-AGENT-ACCESS.md](HOST-OPS-AGENT-ACCESS.md) ثبت شده است. در محیط sandbox فعلی نگهداری دائمی کلید خصوصی در دسترس نیست (`PERSISTENT SSH PRIVATE-KEY STORAGE NOT AVAILABLE`)؛ تا راه‌اندازی runtime دائمی روی میزبان، عملیات از طریق Mode B (WordPress Application Password + رانر تک‌دستور) پشتیبانی می‌شود.
