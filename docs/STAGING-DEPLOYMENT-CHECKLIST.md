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

- [ ] Pending : دسترسی به پنل مدیریت سرور (`cPanel / DirectAdmin / SSH / SFTP`) — وضعیت: `PENDING VENDOR ANSWER` (نیازمند تأیید نهایی هاستینگ `[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`).
- [ ] Pending : تأیید رکوردهای DNS برای ساب‌دامنه استیجینگ (`[PROPOSED: staging.radmansilver.ir — DNS status TBD]`) و دامنه اصلی (`radmansilver.ir`).
- [ ] Pending : صدور و نصب گواهینامه امنیتی SSL (`Let's Encrypt / Wildcard TLS 1.3`).
- [ ] Pending : ایجاد پایگاه داده اختصاصی MySQL / MariaDB و نام کاربری مستقل با دسترسی کامل (`ALL PRIVILEGES`).

---

## 2. PHP & Database Environment Checks (`بررسی نسخه‌ها و اکوسیستم سرور`)

- [ ] Pending : بررسی نسخه PHP (هدف: **`PHP 8.2+`** یا `8.3`).
- [ ] Pending : بررسی نسخه دیتابیس (هدف: **`MySQL 8.0+`** یا **`MariaDB 10.11+`** با Collation استاندارد `utf8mb4_unicode_ci`).
- [ ] Pending : بررسی فعال بودن افزونه‌های حیاتی PHP شامل `cURL`، `mbstring`، `gd` / `imagick`، `zip`، `intl` و `bcmath`.
- [ ] Pending : بررسی تنظیمات حافظه و اجرا (`memory_limit >= 256M`، `max_execution_time >= 120`، `upload_max_filesize >= 32M` — وضعیت: `TBD / PENDING`).

---

## 3. WordPress & WooCommerce Installation (`نصب وردپرس و ووکامرس`)
> **راهنمای نصب خودکار با WP-CLI:** برای اجرای ۱۹ گام نصب وردپرس، ووکامرس و افزونه‌های ضروری با دستورات WP-CLI روی پلن مارس میزبان‌فا به سند [WORDPRESS-INSTALLATION-RUNBOOK.md](WORDPRESS-INSTALLATION-RUNBOOK.md) و اسکریپت [scripts/install_wordpress_mizbanfa.sh](../scripts/install_wordpress_mizbanfa.sh) مراجعه کنید.

- [ ] Pending : نصب هسته وردپرس نسخه `6.x` روی ساب‌دامنه استیجینگ (`[PROPOSED: staging.radmansilver.ir — DNS status TBD]`).
- [ ] Pending : تنظیم زمان سرور روی منطقه زمانی ایران (`Asia/Tehran` - `UTC+3:30`).
- [ ] Pending : نصب و فعال‌سازی افزونه فروشگاه‌ساز **WooCommerce** نسخه پایدار.
- [ ] Pending : تنظیم واحد پول روی **تومان (`Toman`)** و پیکربندی آدرس فروشگاه در تهران.

---

## 4. Required Production Plugins List (`افزونه‌های ضروری مصوب`)

- [ ] Pending : **Persian WooCommerce (`ووکامرس فارسی`)** — جهت تقویم جلالی، شهرهای ایران و نمایش صحیح تومان.
- [ ] Pending : **Blocksy Theme & Blocksy Child Theme** — قالب مینیمال و اشرافی رادمان (پس‌زمینه مشکی مات `#0B0B0E` و متن عاجی `#FAF7F2`).
- [ ] Pending : **Zarinpal Payment Gateway (`درگاه پرداخت زرین‌پال`)** — اتصال به محیط تست/سندباکس جهت پرداخت شبکه شتاب.
- [ ] Pending : **Kavenegar SMS Gateway (`کاوه‌نگار`)** — افزونه پیامک ووکامرس جهت ارسال کد OTP و وضعیت سفارش.
- [ ] Pending : **RankMath SEO** — جهت مدیریت سئو، متاداده‌ها و اسکیمای محصولات.
- [ ] Pending : **Wordfence Security** — فایروال و محافظت در برابر حملات Brute-Force.
- [ ] Pending : **UpdraftPlus Backup** — خودکارسازی بک‌آپ دیتابیس و فایل‌ها.
- [ ] Pending : **Redis Object Cache / LiteSpeed Cache** — در صورت فعال بودن روی سرور میزبان (`Status: PENDING VENDOR ANSWER`).

---

## 5. Staging Domain & Indexing Rules (`محیط استیجینگ و عدم ایندکس`)

- [ ] Pending : استقرار روی ساب‌دامنه مستقل `[PROPOSED: staging.radmansilver.ir — DNS status TBD]` (ایزوله از دامنه اصلی).
- [ ] Pending : **الزام اکید `noindex`:** فعال‌سازی گزینه *«از موتورهای جستجو درخواست کن تا این وب‌سایت را بررسی نکنند»* در تنظیمات خواندن وردپرس و تنظیم هدر `X-Robots-Tag: noindex, nofollow` در Nginx/LiteSpeed جهت جلوگیری از ایندکس شدن استیجینگ در گوگل.

---

## 6. Admin Account Hardening & Security (`مقاوم‌سازی امنیتی مدیریت`)

- [ ] Pending : حذف شناسه کاربری پیش‌فرض `admin` و ایجاد کاربر مدیر کل با نام کاربری اختصاصی و رمز عبور قدرتمند.
- [ ] Pending : تغییر مسیر ورود پیش‌فرض (`/wp-login.php`) به مسیر مخفی اختصاصی توسط Wordfence.
- [ ] Pending : فعال‌سازی احراز هویت دو مرحله‌ای (`2FA`) برای تمامی حساب‌های مدیر.

---

## 7. Configuration Separation: `wp-config.php` vs `.env` (`جداسازی اطلاعات حساس`)

- **اصل جداسازی امنیتی:** تمامی اطلاعات محرمانه وب‌سرویس‌ها (کلیدهای Zarinpal Merchant ID، کاوه‌نگار API Key، توکن تلگرام و کلیدهای ووکامرس) باید **منحصراً در فایل `.env` ریشه** نگهداری شوند و هرگز در کد قالب یا دیتابیس هاردکد نشوند.
- [ ] Pending : تأیید وجود فایل `.env` در ریشه سرور و ممنوعیت دسترسی وب (`chmod 600` و مسدودسازی در `.htaccess` / `nginx.conf`).

---

## 8. Technical Verification & Integration Tests (`آزمون‌های فنی زیرساخت`)

- [ ] Pending : **Media Upload Test:** آپلود یک تصویر نمونه مربع ۱:۱ (`1600x1600 px`) جهت بررسی تبدیل خودکار به WebP و سلامت کتابخانه `Imagick`.
- [ ] Pending : **REST API Test:** ارسال درخواست احراز هویت‌شده به مسیر `/wp-json/wc/v3/products` جهت تأیید کارکرد صحیح API و عدم مسدودسازی توسط ModSecurity / WAF.
- [ ] Pending : **WooCommerce Webhook Test:** ایجاد وب‌هوک تست `order.created` و ارسال به اندپوینت تلگرام جهت تأیید عدم فیلتر خروجی `cURL` روی پورت 443.
- [ ] Pending : **Backup Test:** تهیه یک نسخه پشتیبان دستی آزمایشی توسط UpdraftPlus و بررسی صحت ذخیره‌سازی.

---

## 9. Staging Deployment Sign-Off Table (`جدول تأییدیه استقرار آزمایشی`)

| Item | Owner | Status | Notes |
| :--- | :---: | :---: | :--- |
| **Server & Hosting Provisioning** | Technical Lead / Hosting Admin | `PENDING VENDOR ANSWER` | Iranian hosting confirmation (`[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`) |
| **PHP 8.2+ & MySQL 8.0+ Verification** | DevOps Lead | `PENDING VENDOR ANSWER` | Verify mbstring, cURL, imagick, bcmath |
| **WordPress & WooCommerce Setup** | E-Commerce Developer | `NOT YET TESTED` | Blocksy Child theme & Persian localization |
| **Staging noindex Enforcement** | SEO Strategist | `NOT YET TESTED` | Prevent Google indexing of `[PROPOSED: staging.radmansilver.ir — DNS status TBD]` |
| **Security Hardening & .env Separation** | Security Lead | `NOT YET TESTED` | Wordfence setup, zero cleartext secrets |
| **REST API & Webhook Verification** | Automation Agent Lead | `NOT YET TESTED` | Verify WooCommerce REST API v3 & Telegram webhook |
