# سیاست‌های امنیتی و محافظت از فروشگاه (`SECURITY.md`)

This document defines the WordPress/WooCommerce hardening rules, firewall policies, secret encryption, and UpdraftPlus backup schedules for `radman-silver-store`.

---

## 1. WordPress Core & WooCommerce Hardening (`امنیت هسته وردپرس`)

- **Disable XML-RPC:** Strictly disable `/xmlrpc.php` via Nginx configuration to block brute-force amplification attacks.
- **Custom Admin Login URL:** Rename default `/wp-admin` and `/wp-login.php` to a secret administrative slug.
- **Content Security Policy (CSP):** Enforce strict CSP headers preventing unauthorized inline scripts or third-party tracking pixels.
- **Login Rate Limiting:** Wordfence automatically blocks any IP address after 5 failed login attempts within 10 minutes.

---

## 2. Secret Key Management & Zero Cleartext Credential Rule (`مدیریت کلیدهای امنیتی`)

- **Strict Exclusion Rule:** All Zarinpal Merchant IDs, Kavenegar SMS API keys, Telegram Bot Tokens, and `noghrehmashhad.ir` API credentials MUST reside strictly in root `.env`.
- **Git Ignore Verification:** Ensure `.env`, `.env.local`, and `*.log` are strictly declared in `.gitignore`.
- **Never expose credentials** in Telegram error messages or public HTTP debug logs.

---

## 3. UpdraftPlus Automated Backup Schedule (`زمان‌بندی نسخه‌برداری پشتیبان`)

| Backup Component | Schedule | Target Cloud Storage | Retention Period |
| :--- | :--- | :--- | :--- |
| **Database (WooCommerce Orders & Products)** | **Daily at 03:00 AM** | ArvanCloud S3 Object Storage | 30 Days |
| **Full Filesystem (Theme, Media, Plugins)** | **Weekly on Sunday 02:00 AM** | ArvanCloud S3 Object Storage | 4 Weeks |
