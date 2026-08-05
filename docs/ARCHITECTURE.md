# معماری فنی سیستم (`ARCHITECTURE.md`)

This document defines the high-level system architecture, software boundaries, database integrations, hosting specifications, and API communication protocols for **RADMAN SILVER STORE (`radman-silver-store`)**.

---

## 1. System Overview Diagram (`معماری کلان سیستم`)

```text
+---------------------------------------------------------------------------------------------------+
|                                  CLIENT & STOREFRONT LAYER                                        |
|                                                                                                   |
|  [ Customer Web Browser ]     [ Mobile Viewport (Responsive) ]       [ Instagram / Telegram ]     |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                      HTTPS (TLS 1.3) / REST
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                           CLOUDFLARE / ARVANCLOUD EDGE CDN & WAF                                  |
|   - DDOS Protection        - SSL Termination        - Full-Page Caching        - WebP Compression |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                             WORDPRESS & WOOCOMMERCE CORE ENGINE                                   |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | BLOCKS-Y LUXURY THEME   |  RankMath SEO  |  Persian WooCommerce  |  Zarinpal / Kavenegar  |  |
|  | - Matte Black #0B0B0E   |  - Schema.org  |  - Jalali Dates       |  - Payment Gateway     |  |
|  | - Ivory Typography      |  - XML Sitemap |  - Iranian Towns      |  - SMS Notifications   |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  ^                                                |
|                                                  | WooCommerce REST API v3                        |
+--------------------------------------------------+------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|                         PYTHON 3.11+ ASYNC AUTOMATION AGENT RUNNERS                               |
|                                                                                                   |
|  +--------------------+   +--------------------+   +--------------------+   +------------------+  |
|  | Agent-LegacySync   |   | Agent-Pricing      |   | Agent-OrderApproval|   | Agent-Media      |  |
|  | - Scrapes Legacy   |   | - Silver Gram Rate |   | - Telegram Alert   |   | - 1:1 Crop WebP  |  |
|  | - Creates Drafts   |   | - Margin Calculation|  | - Owner Button     |   | - Logo Watermark |  |
|  +--------------------+   +--------------------+   +--------------------+   +------------------+  |
+------------+-------------------------+------------------------------+-----------------------------+
             |                         |                              |
             v                         v                              v
+------------------------+  +--------------------------+  +-----------------------------------------+
|  LEGACY STORE API      |  |  TELEGRAM BOT GATEWAY    |  |  EXTERNAL SERVICES & GATEWAYS           |
|  (noghrehmashhad.ir)   |  |  (@RadmanSilverStoreBot) |  |  - Zarinpal Payment API (Shetab)        |
|  - Raw SKU & Stock     |  |  - Human-in-the-Loop     |  |  - Kavenegar SMS OTP / Order Alerts     |
|  - Legacy Catalog      |  |  - Interactive Buttons   |  |  - Tehran Gold/Silver Market API        |
+------------------------+  +--------------------------+  +-----------------------------------------+
```

---

## 2. Core Components & Responsibilities (`اجزای اصلی سیستم`)

1. **WordPress 6.x + WooCommerce Core:**
   - Serves as the primary content management system and transactional e-commerce engine.
   - Hosts Blocksy Child Theme with customized RTL Estedad Bold and Didot typography.
   - Manages customer sessions, shopping carts, checkout workflows, and order persistence.
2. **WooCommerce REST API v3:**
   - Exposes authenticated HTTPS endpoints (`/wp-json/wc/v3/products`, `/orders`, `/media`) for Python automation agents.
   - Uses dedicated API Consumer Key and Consumer Secret with least-privilege scoping.
3. **Python 3.11+ Automation Agent Daemon:**
   - Standalone asynchronous Python service running via `systemd` or Docker container on the host server.
   - Operates scheduled cron tasks for legacy catalog sync, daily silver pricing calculation, and order monitoring.
4. **Local SQLite / PostgreSQL Staging Database:**
   - Maintains a local state table (`legacy_sync_map.db`) tracking mapping between `noghrehmashhad.ir` legacy ID and WooCommerce Product ID.
   - Prevents duplicate product creation and logs sync timestamp checksums.

---

## 3. Hosting & Infrastructure Specifications (`مشخصات زیرساخت و سرور`)

- **Server Location & Provider:** **Iran Server Sonic 30** (Linux Cloud Hosting in Iranian data center for ultra-low latency Shetab payments and Enamad compliance).
- **Web Server Engine:** Nginx Reverse Proxy fronting LiteSpeed / PHP-FPM 8.2+.
- **Database Engine:** MySQL 8.0+ / MariaDB 10.11+ with InnoDB UTF-8MB4 collation (`utf8mb4_unicode_ci`) for flawless Persian typography and emoji support.
- **SSL / Security Layer:** Let's Encrypt Wildcard SSL certificate enforcing TLS 1.3 cipher suites.
- **CDN & Edge Caching:** Cloudflare / ArvanCloud enterprise WAF enabled:
  - Cache HTML pages for anonymous visitors (`TTL: 1 hour`).
  - Bypass caching for `/checkout/`, `/cart/`, `/my-account/`, and `/?add-to-cart=`.

---

## 4. Security & Integration Boundaries (`مرزهای امنیتی و دسترسی‌ها`)

- **Zero Cleartext Secrets:** All WordPress DB credentials, WooCommerce API keys, Telegram Bot Tokens, Zarinpal Merchant IDs, and Kavenegar API keys must reside strictly in root `.env` (excluded from git via `.gitignore`).
- **Webhook Authorization:** Telegram webhook requests are validated against official Telegram IP CIDR ranges and secret token headers.
- **API Rate Limiting:** All automation agents implement exponential backoff and rate limiting (`max 2 requests/second`) against WooCommerce REST API to prevent server CPU spikes.
