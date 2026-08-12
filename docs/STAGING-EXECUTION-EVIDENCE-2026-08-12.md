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
- **Installed/Active plugins (8):**
  - `blocksy-companion 2.1.52`
  - `gateland 2.4.5` *(installed only; payment configuration PENDING)*
  - `litespeed-cache 7.9`
  - `seo-by-rank-math 1.0.275`
  - `updraftplus 1.26.6`
  - `woocommerce 11.0.1`
  - `wordfence 9.0.0`
  - `persian-woocommerce 10.0.4`
- **WooCommerce currency & Currency Safety Gate:**
  - **Terminal-observed currency: IRR. Owner selected Toman in WooCommerce UI. Currency Safety Gate remains PENDING to verify storage/display/schema conversion before product import, pricing sync, or payment testing.**
  - WooCommerce currency position: `right`
  - WooCommerce decimals: `0`
- **Payment Gateway Tooling:**
  - **Gateland is installed but payment configuration is PENDING. No live payment is configured.**
- **Database check:** `Success` (one informational note on `wp_wfls_role_counts` storage engine — non-blocking)
- **SSL:** Let's Encrypt certificate active on `staging.radmansilver.ir`
- **HTTPS check:** `HTTP/2 200`, LiteSpeed server, `x-litespeed-cache hit`
- **wp-admin login:** **wp-admin login verified by owner; admin credentials rotated; no admin password stored in repository.** (verified using safe documented identifier `radmanadmin`)
- **Post-install security:** database password and WordPress admin password were rotated by owner AFTER initial install
- **Secret storage & env-loader state:** **Current DB credential state: standard WordPress wp-config.php DB constants are in use for staging compatibility. Private staging.env also exists outside web root with chmod 600. Full env-loader migration remains PENDING hardening.**
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
- **Gateland is installed but payment configuration is PENDING. No live payment is configured.**

---

## 3. Still Pending Items (`موارد موکول‌شده به مأموریت‌های آتی`)

The following items remain strictly **PENDING** across all repository documentation:
- **Redis object cache activation (`PENDING HOST REDIS CONFIGURATION`)**
- **Currency Safety Gate verification (`Terminal-observed currency: IRR; owner selected Toman in WooCommerce UI; storage/display/schema behavior must be verified before product import, pricing sync, or payment testing`)**
- **Full env-loader migration / removal of DB password from `wp-config.php` (`PENDING hardening`)**
- **Product import**
- **Pricing agent activation**
- **Live payment gateway configuration (`Gateland / Zarinpal configuration PENDING`)**
- **Live SMS sending to customers (`Kavenegar`)**
- **Python agent deployment**
- **Production deployment (`public_html` untouched)**
