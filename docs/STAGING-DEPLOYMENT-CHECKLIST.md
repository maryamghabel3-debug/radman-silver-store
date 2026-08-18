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
- [x] `DONE (repo)` : **محتوای کامل ۱۱ صفحه** در `content/static-pages/` نوشته شده و با `scripts/check_no_placeholders.py` تأیید شده که placeholder-free است (همهٔ تعهدهای عملیاتی تأییدنشده حذف و به‌صورت مشروط/پیش‌نویس بازنویسی شده‌اند).
- [x] `DONE (repo)` : **ابزار یک‌دستوری پایه فروشگاه** (`scripts/build_staging_storefront.sh`) آماده است: بک‌آپ + child theme sync + ۱۱ صفحه Draft + homepage Gutenberg foundation + ۳ دسته‌بندی محصول + منوی اصلی + گزارش وضعیت WooCommerce/LiteSpeed. همگی `--plan` پیش‌فرض، idempotent، و فاقد هرگونه فعال‌سازی پرداخت/پیامک/ردیس/انتشار هستند.
- [ ] `PENDING (host execution)` : **اجرای یک دستور نهایی روی میزبان** (توسط مالک از داخل ایران) — مطابق [FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md](FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md):
  ```bash
  export PATH="$HOME/bin:$PATH"
  APP_ENV=staging \
  CONFIRM_STAGING_APPLY=YES \
  WP_PATH=/home/radmansi/staging.radmansilver.ir \
  WP_URL=https://staging.radmansilver.ir \
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
  bash /home/radmansi/radman-deploy/repo/scripts/build_staging_storefront.sh --apply-staging
  ```
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
- [x] `DONE (repo)` : gate محتوای کامل (بدون placeholder) با `scripts/check_no_placeholders.py` در هر اجرای plan اعمال می‌شود. gate فقط روی `[…]` (براکت+بیضی) و کلاس `radman-placeholder` fail می‌کند؛ بیضی عادی `…` در نثر فارسی مجاز است.
- [x] `DONE (repo)` : self-test محلی `scripts/test_plan_runner.sh` اجرای plan، چاپ جدول DEPLOY PLAN، عدم وجود placeholder، و تست‌های رگرسیون بیضی/`[…]`/کلاس/لینک فارسی را شامل می‌شود.
- [x] `DONE (repo)` : رجیستری تأیید محتوا در [docs/STATIC-CONTENT-APPROVAL-REGISTRY.md](STATIC-CONTENT-APPROVAL-REGISTRY.md) ایجاد شد (همه ۱۱ صفحه: Draft deploy YES، Publish BLOCKED).
- [x] `DONE (repo)` : self-test نهایی `scripts/test_storefront_batch.sh` شامل 83 تست پاس می‌شود (نگهبانی پیش‌فرض plan، لزوم CONFIRM، رد public_html، DRAFT ماندن همه صفحات، صفحه اصلی = ID 18، دسته‌بندی‌ها rings/necklaces/bracelets، منوی مصوب، عدم فعال‌سازی پرداخت/پیامک/ردیس، عدم نشت secret، اعتبارسنجی Gutenberg و رگرسیون بیضی فارسی).
- [ ] `PENDING host execution` : اجرای **یک دستور نهایی** `bash scripts/build_staging_storefront.sh --plan` (dry run) روی میزبان توسط مالک و بررسی خروجی.
- [ ] `PENDING host execution` : اجرای **یک دستور نهایی** `bash scripts/build_staging_storefront.sh --apply-staging` با `CONFIRM_STAGING_APPLY=YES` (بک‌آپ خودکار + child theme sync + ۱۱ صفحه Draft + homepage + دسته‌بندی‌ها + منو + گزارش WooCommerce/LiteSpeed).
- [ ] `PENDING OWNER OPERATIONAL APPROVAL` : تأیید نهایی مالک برای محتوای تمام ۱۱ صفحه (اطلاعات تماس/ساعت، روش‌های ارسال، بسته‌بندی، SLA، قیمت‌گذاری، سنگ‌های موجود و ...).
- [ ] `PENDING LEGAL REVIEW` : بازبینی حقوقی برای صفحات `returns`، `privacy-policy-radman` و `terms` قبل از هرگونه انتشار عمومی.
- [ ] `BLOCKED` : انتشار عمومی (Publish) هر یک از ۱۱ صفحه تا زمانی که Owner approval = APPROVED و (در صورت نیاز) Legal review = APPROVED باشد.

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
