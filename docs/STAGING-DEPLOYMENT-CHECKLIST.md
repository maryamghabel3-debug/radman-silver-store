# چک‌لیست استقرار و پیکربندی محیط آزمایشی (`STAGING-DEPLOYMENT-CHECKLIST.md`)

> **راهنمای اجرایی استقرار وردپرس و ووکامرس در محیط استیجینگ (Staging Setup Checklist)**  
> *این چک‌لیست مراحل گام‌به‌گام نصب، مقاوم‌سازی، تست و پیکربندی فروشگاه رادمان سیلور (`radman-silver-store`) را قبل از ورود به سرور پروداکشن پوشش می‌دهد.*

> **راهنمای وضعیت‌های چک‌لیست (Status Definitions):**  
> - **`CONFIRMED`**: تأییدشده و نهایی  
> - **`PENDING VENDOR ANSWER`**: در انتظار پاسخ فنی پشتیبانی هاستینگ (میزبان‌فا / پارس‌پک)  
> - **`PENDING OWNER DECISION`**: در انتظار تصمیم یا تأیید مالک برند  
> - **`NOT YET TESTED`**: هنوز تست نشده (آماده برای تست در استیجینگ/پروداکشن)  
> - **`NOT APPLICABLE`**: غیرقابل اعمال / بلاموضوع  

---

## 1. Server Access Prerequisites (`پیش‌نیازهای دسترسی سرور`)

- [x] DONE : دسترسی به پنل مدیریت سرور (`cPanel / DirectAdmin / SSH / SFTP`) — وضعیت: `DONE` (تأییدشده روی پلن مارس میزبان‌فا، کاربر cPanel: `radmansi`، سرور LiteSpeed).
- [x] DONE : تأیید رکوردهای DNS برای ساب‌دامنه استیجینگ (`staging.radmansilver.ir`) و دامنه اصلی (`radmansilver.ir`).
- [x] DONE : صدور و نصب گواهینامه امنیتی SSL (`Let's Encrypt` فعال روی `staging.radmansilver.ir`، بررسی HTTPS: `HTTP/2 200`، هدر `x-litespeed-cache hit`).
- [x] DONE : ایجاد پایگاه داده اختصاصی MySQL / MariaDB و نام کاربری مستقل (`radmansi_staging_wp` / `radmansi_staging_user` با دسترسی کامل؛ صحت اتصال تأیید شد).

---

## 2. PHP & Database Environment Checks (`بررسی نسخه‌ها و اکوسیستم سرور`)

- [x] DONE : بررسی نسخه PHP (تأییدشده: **`PHP 8.2.31`**).
- [x] DONE : بررسی نسخه دیتابیس (تأییدشده: **`MariaDB 11.4.12-MariaDB`**).
- [x] DONE : بررسی ابزارهای خط فرمان و پایتون (تأییدشده: `WP-CLI 2.12.0`، `Python 3.11.15` در `/opt/alt/python311/bin/python3.11` و `pip 21.3.1`).
- [x] DONE : بررسی صحت عملکرد دیتابیس (`wp db check: Success` — یک یادداشت اطلاعاتی غیرمسدودکننده درباره موتور ذخیره‌سازی `wp_wfls_role_counts`).

---

## 3. WordPress & WooCommerce Installation (`نصب وردپرس و ووکامرس`)
> **مستندات تأییدشده استقرار استیجینگ:** گزارش کامل شواهد تأییدشده استقرار استیجینگ رادمان سیلور در سند [STAGING-EXECUTION-EVIDENCE-2026-08-12.md](STAGING-EXECUTION-EVIDENCE-2026-08-12.md) ثبت شده است.

- [x] DONE : نصب هسته وردپرس روی ساب‌دامنه استیجینگ (تأییدشده: نسخه **`WordPress 7.0.3`** روی `https://staging.radmansilver.ir`).
- [x] DONE : تنظیم زمان سرور روی منطقه زمانی ایران (`Asia/Tehran`).
- [x] DONE : تنظیم زبان روی فارسی (`fa_IR`) و ساختار پیوند یکتا روی `/%postname%/`.
- [x] DONE : نصب و فعال‌سازی افزونه فروشگاه‌ساز **WooCommerce** (تأییدشده: نسخه **`11.0.1`**).
- [x] DONE : تنظیم واحد پول روی **`IRR` (ریال)**، موقعیت راست (`right`) و صفر اعشار (`0 decimals`).
- [x] DONE : **دروازه امنیتی واحد پول (`Currency Safety Gate` - CLOSED / VERIFIED):** ورود مستقیم قیمت به **تومان (Toman)** به عنوان رفتار صحیح و تأییدشده قفل و اعمال شده است (`Toman direct input is verified as correct`).
- [x] DONE : **Static pages creation:** ایجاد ۱۱ صفحه استاتیک فارسی به عنوان پیش‌نویس (`Draft`) با شناسه‌های واقعی ۲۱ تا ۳۱ در وردپرس استیجینگ تأیید شد (`Page IDs 21 to 31 drafted`). همچنین صفحه اصلی با شناسه ۱۸ منتشر و تنظیم شد.

---

## 4. Required Production Plugins List (`افزونه‌های ضروری مصوب`)

- [x] DONE : **Persian WooCommerce (`ووکامرس فارسی`)** — فعال و تأییدشده (نسخه `10.0.4`).
- [x] DONE : **Blocksy Theme (`blocksy 2.1.52`) & Blocksy Companion (`2.1.52`)** — قالب مینیمال رادمان نصب و فعال شد.
- [x] DONE : **Blocksy Child Theme** — قالب فرزند با استایل‌های مشکی مات `#0B0B0E` و عاجی `#FAF7F2` روی استیجینگ ایجاد و فعال شد (`blocksy-child v1.0.0 active`).
- [x] DONE : **Gateland Payment Gateway (`gateland 2.4.5`)** — نصب‌شده روی استیجینگ (`Gateland 2.4.5 installed on staging`).
- [ ] PENDING : **Gateland & Zarinpal Payment Gateway Configuration** — پیکربندی درگاه پرداخت و هرگونه پرداخت زنده در وضعیت `PENDING` است.
- [ ] PENDING : **Kavenegar SMS Gateway (`کاوه‌نگار`)** — یکپارچه‌سازی وب‌سرویس پیامک در وضعیت `PENDING` است.
- [x] DONE : **RankMath SEO (`seo-by-rank-math 1.0.275`)** — نصب و فعال شد (اجرای ویزارد تنظیمات اولیه به مأموریت آتی موکول شد: `PENDING`).
- [x] DONE : **Wordfence Security (`wordfence 9.0.0`)** — نصب و فعال شد (تنظیمات سخت‌گیرانه فایروال: `PENDING`).
- [x] DONE : **UpdraftPlus Backup (`updraftplus 1.26.6`)** — نصب و فعال شد (تنظیم مقصد فضای ابری بک‌آپ: `PENDING`).
- [x] DONE : **LiteSpeed Cache (`litespeed-cache 7.9`)** — نصب و فعال شد (تنظیمات پیشرفته کش: `PENDING`).
- [ ] PENDING : **Redis Object Cache** — فعال‌سازی کش آبجکت در وضعیت `PENDING HOST REDIS CONFIGURATION` قرار دارد.
- [ ] PENDING : **WooCommerce Onboarding Wizard** — ویزارد راه‌اندازی اولیه ووکامرس به مأموریت آتی موکول شد (`PENDING`).

---

## 5. Staging Domain & Indexing Rules (`محیط استیجینگ و عدم ایندکس`)

- [x] DONE : استقرار روی ساب‌دامنه مستقل `https://staging.radmansilver.ir` (ایزوله از دامنه اصلی و پروداکشن).
- [x] DONE : **الزام اکید `noindex`:** تأیید فعال بودن گزینه عدم ایندکس روی استیجینگ (`blog_public = 0` / `noindex confirmed`).

---

## 6. Admin Account Hardening & Security (`مقاوم‌سازی امنیتی مدیریت`)

- [x] DONE : صحت کارکرد ورود به پیشخوان مدیریت وردپرس (`wp-admin login verified by owner` با شناسه امن `radmanadmin`).
- [x] DONE : چرخش رمزهای عبور پس از نصب اولیه (`passwords rotated after initial install`؛ هیچ رمزی در مخزن ذخیره نشده است).
- [x] DONE : ایجاد فایل محیطی امن خارج از ریشه وب (`private staging.env exists outside web root with chmod 600`).
- [ ] PENDING : مهاجرت کامل به لودر محیطی در `wp-config.php` و حذف رمز عبور دیتابیس از `wp-config.php` (`full wp-config env-loader migration / removal of DB password from wp-config.php`).
- [ ] PENDING : فعال‌سازی احراز هویت دو مرحله‌ای (`2FA`) و قوانین سخت‌گیرانه Wordfence.

---

## 7. Configuration Separation: `wp-config.php` vs `.env` (`جداسازی اطلاعات حساس`)

- [x] DONE : تأیید نگهداری اطلاعات حساس در مسیر خصوصی خارج از پوشه وب (`/home/radmansi/.config/radman/staging.env` با دسترسی `chmod 600`).
- [ ] PENDING : مهاجرت کامل `wp-config.php` به لودر محیطی `.env` و حذف ثابت‌های پسورد دیتابیس از `wp-config.php` (`PENDING hardening`).

---

## 8. Technical Verification & Integration Tests (`آزمون‌های فنی زیرساخت`)

- [x] DONE : **Database & Server Verification:** صحت عملکرد دیتابیس (`wp db check: Success`) و وب‌سرویس `HTTPS HTTP/2 200` با کش LiteSpeed تأیید شد.
- [ ] PENDING : **Media Upload Test & WebP Conversion**
- [ ] PENDING : **REST API Test (`/wp-json/wc/v3/products`)**
- [ ] PENDING : **WooCommerce Webhook & Telegram Notification Test**
- [ ] PENDING : **Backup Destination Test**
- [ ] PENDING : **Python Agent Runtime Deployment (`agents/` scripts)**
- [ ] PENDING : **Product Import & Pricing Agent Activation**
- [ ] PENDING : **Production Deployment (`public_html` untouched)**

---

## 9. Staging Deployment Sign-Off Table (`جدول تأییدیه استقرار آزمایشی`)

| Item | Owner | Status | Notes |
| :--- | :---: | :---: | :--- |
| **Server & Hosting Provisioning** | Technical Lead / Hosting Admin | `DONE` | Verified on MizbanFa Mars plan (`cPanel: radmansi`, LiteSpeed server, `staging.radmansilver.ir`) |
| **PHP 8.2+ & MariaDB Verification** | DevOps Lead | `DONE` | Verified `PHP 8.2.31`, `MariaDB 11.4.12`, `WP-CLI 2.12.0`, `Python 3.11.15` |
| **WordPress & WooCommerce Setup** | E-Commerce Developer | `DONE` | Verified `WP 7.0.3`, `WooCommerce 11.0.1`, `blocksy-child v1.0.0 active`, 11 static pages drafted (IDs 21-31), Home page (ID 18) static front page |
| **Staging noindex Enforcement** | SEO Strategist | `DONE` | Verified `blog_public = 0` (`noindex confirmed`) |
| **Security Hardening & .env Separation** | Security Lead | `DONE` | Passwords rotated post-install; secret stored at `/home/radmansi/.config/radman/staging.env` (`chmod 600`) |
| **REST API, Webhook & Agent Runtime** | Automation Agent Lead | `PENDING` | Python agent deployment, SMS/Zarinpal integrations remain PENDING (Currency Safety Gate CLOSED / VERIFIED) |
