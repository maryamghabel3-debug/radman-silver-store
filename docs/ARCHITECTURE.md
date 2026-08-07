# معماری فنی سیستم (`ARCHITECTURE.md`)

This document defines the high-level system architecture, software boundaries, database integrations, hosting specifications, and API communication protocols for **RADMAN SILVER STORE (`radman-silver-store`)**.

---

## 1. System Overview Diagram (`معماری کلان سیستم`)

```text
+---------------------------------------------------------------------------------------------------+
|                                  CLIENT & STOREFRONT LAYER                                        |
|  [ Customer Web Browser ]     [ Mobile Viewport (Responsive) ]       [ Instagram / Telegram ]     |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                      HTTPS (TLS 1.3) / REST
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                             WORDPRESS & WOOCOMMERCE CORE ENGINE                                   |
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
|               PYTHON 3.11+ ASYNC AUTOMATION AGENTS (HOSTED ON IRAN SERVER SONIC 30)               |
|                                                                                                   |
|  +--------------------+   +--------------------+   +--------------------+   +------------------+  |
|  | Agent-LegacySync   |   | Agent-Pricing      |   | Agent-OrderApproval|   | Agent-Media      |  |
|  | - 1:1 Exact Stock  |   | - Simple Daily Rate|   | - Telegram HITL    |   | - 1:1 Crop WebP  |  |
|  | - Admin Panel API  |   | - Weight * Rate    |   | - Owner Button     |   | - Logo Watermark |  |
|  +--------------------+   +--------------------+   +--------------------+   +------------------+  |
+------------+-------------------------+------------------------------+-----------------------------+
             |                         |                              |
             v                         v                              v
+------------------------+  +--------------------------+  +-----------------------------------------+
|  LEGACY ADMIN API      |  |  TELEGRAM BOT GATEWAY    |  |  EXTERNAL SERVICES & GATEWAYS           |
|  (noghrehmashhad.ir)   |  |  (@RadmanSilverStoreBot) |  |  - Zarinpal Payment API (Shetab)        |
|  - Read-Only GET Audit |  |  - Daily Rate Input (/price)|  - Kavenegar SMS OTP / Order Alerts     |
|  - Exact Stock (1=1)   |  |  - Order Fulfillment Confirmation                             |
+------------------------+  +--------------------------+  +-----------------------------------------+
```

---

## 2. Core Operational Realities

1. **Iranian Hosting Infrastructure:** All automation agents execute on **Iran Server Sonic 30** Linux cloud hosting inside Iran to ensure uninterrupted access to both `noghrehmashhad.ir` Admin Panel API and Shetab banking gateways.
2. **1:1 Stock Reality:** Radman Silver maintains its own Inventory Registry. `Stock = 1` is sellable and synced exactly (`1:1 mapping`; zero buffers).
3. **Simple Daily Rate Pricing:** The owner inputs one daily silver gram rate via Telegram (`نرخ امروز هر گرم نقره = X تومان`). Weight-based products compute retail price as `weight * daily_rate`.
