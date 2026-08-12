# گزارش شواهد استقرار موفقیت‌آمیز محیط آزمایشی رادمان سیلور (`STAGING-EXECUTION-EVIDENCE-2026-08-12.md`)

> **گزارش مستندات تأییدشدهٔ استقرار واقعی وردپرس، ووکامرس و افزونه‌های مصوب روی ساب‌دامنه استیجینگ پلن مارس میزبان‌فا**  
> *این سند نتایج تأییدشدهٔ اجرای دستی استقرار توسط مالک روی سرور میزبان‌فا را ثبت می‌کند. هیچ‌گونه اطلاعات محرمانه (رمزهای عبور، توکن‌ها یا کلیدهای وب‌سرویس) در این سند و مخزن نگهداری نمی‌شود.*

---

## 1. Verified Real Results (from Owner's Actual Terminal Session)

- **Date:** `2026-08-12` (`Asia/Tehran` timezone)
- **Host:** MizbanFa Mars plan, cPanel user `radmansi`
- **Server:** `LiteSpeed`
- **PHP version:** `8.2.31`
- **WP-CLI version:** `2.12.0`
- **MariaDB server version:** `11.4.12-MariaDB` *(برتری نسبت به نسخه پایه اعلامی `10.3`)*
- **Python Runtime:** `3.11.15` available at `/opt/alt/python311/bin/python3.11`
- **pip:** `21.3.1` installed for Python 3.11
- **WordPress core version:** `7.0.3`
- **Site URL:** `https://staging.radmansilver.ir`
- **blog_public:** `0` (`noindex confirmed`)
- **Timezone:** `Asia/Tehran`
- **Locale:** `fa_IR`
- **Permalink structure:** `/%postname%/`
- **Active theme:** `blocksy 2.1.52`
- **Active plugins (7):**
  - `blocksy-companion 2.1.52`
  - `litespeed-cache 7.9`
  - `seo-by-rank-math 1.0.275`
  - `updraftplus 1.26.6`
  - `woocommerce 11.0.1`
  - `wordfence 9.0.0`
  - `persian-woocommerce 10.0.4`
- **WooCommerce currency:** `IRR`
- **WooCommerce currency position:** `right`
- **WooCommerce decimals:** `0`
- **Database check:** `Success` (one informational note on `wp_wfls_role_counts` storage engine — non-blocking)
- **SSL:** Let's Encrypt certificate active on `staging.radmansilver.ir`
- **HTTPS check:** `HTTP/2 200`, LiteSpeed server, `x-litespeed-cache hit`
- **wp-admin login:** verified working by owner (using safe documented identifier `radmanadmin`)
- **Post-install security:** database password and WordPress admin password were rotated by owner AFTER initial install
- **Secret storage:** `DB_PASSWORD` stored in `wp-config.php` (`chmod 664`) and in `/home/radmansi/.config/radman/staging.env` (`chmod 600`, private path outside web root)
- **Redis:** NOT YET CONFIGURED — remains `PENDING HOST REDIS CONFIGURATION`

---

## 2. Explicit Operational & Safety Notes (`یادداشت‌های صریح عملیاتی و امنیتی`)

- **Staging only — production (`public_html`) untouched**
- **No product import performed**
- **No pricing sync performed**
- **No live payment configured**
- **No customer SMS sending activated**
- **No Python agent deployed yet**
- **Passwords rotated post-installation; not stored in repository**
- **Currency safety gate remains a blocker for any product/price operation**

---

## 3. Still Pending Items (`موارد موکول‌شده به مأموریت‌های آتی`)

The following items remain strictly **PENDING** across all repository documentation:
- **Redis object cache activation (`PENDING HOST REDIS CONFIGURATION`)**
- **Currency safety gate verification (Toman vs IRR conversion test)**
- **Product import**
- **Pricing agent activation**
- **Live payment gateway configuration (`Zarinpal`)**
- **Live SMS sending to customers (`Kavenegar`)**
- **Python agent deployment**
- **Production deployment (`public_html` untouched)**
