# استراتژی و معماری ایجنت‌های اتوماسیون (`AGENT-STRATEGY.md`)

This document defines the governance philosophy, event orchestration, and human-in-the-loop controls for the AI automation agents operating in **RADMAN SILVER 925**.

---

## 1. Executive Summary & Design Philosophy (`اصول حاکمیت هوش مصنوعی`)

The RADMAN SILVER automation ecosystem operates under a strict **Human-in-the-Loop (`HITL`) Governance Model**:
> *“Agents propose, calculate, and prepare; the human owner approves, confirms, and publishes.”*

In Phase 1, zero automated actions that alter storefront prices, publish new products, or fulfill customer orders occur without explicit confirmation from the business owner via Telegram interactive buttons.

---

## 2. Agent Ecosystem & Workflow Interconnects (`نقشه تعاملی ایجنت‌ها`)

```text
    +---------------------------------------------------------------------------------+
    |                                EVENT BUS / REDIS                                |
    +---+-------------------+-------------------+-------------------+-------------+---+
        |                   |                   |                   |             |
        v                   v                   v                   v             v
+---------------+   +---------------+   +---------------+   +---------------+   +---------------+
| Agent-        |   | Agent-        |   | Agent-        |   | Agent-        |   | Agent-        |
| LegacySync    |   | Pricing       |   | OrderApproval |   | Media         |   | Support       |
+---------------+   +---------------+   +---------------+   +---------------+   +---------------+
        |                   |                   |                   |             |
        +-------------------+-------------------+-------------------+-------------+
                                                |
                                                v
                              +-----------------------------------+
                              |       TELEGRAM BOT GATEWAY        |
                              |     (Owner Approval Interface)    |
                              +-----------------------------------+
```

### Agent Responsibilities Table

| Agent Name | Core Mandate | Execution Trigger | Human Approval Required? | Output Target |
| :--- | :--- | :--- | :--- | :--- |
| **`Agent-LegacySync`** | Extract catalog & stock from `noghrehmashhad.ir` | Twice daily cron / `/sync_now` | **YES** (Creates Drafts only) | WooCommerce DB (`Drafts`) |
| **`Agent-Pricing`** | Fetch daily silver gram rate & compute retail price | Daily at 10:30 AM Tehran | **YES** (Telegram Price Confirmation) | WooCommerce Product Prices |
| **`Agent-OrderApproval`** | Notify owner of new orders & verify fulfillment | Instant upon checkout | **YES** (Telegram Order Confirmation) | WooCommerce Order Status |
| **`Agent-Media`** | Crop 1:1, convert WebP & apply subtle watermark | On new draft creation | **NO** (Automated processing) | WordPress Media Library |
| **`Agent-Support`** | Answer standard sizing/care FAQ via rule engine | On user chat message | **NO** (Escalates to human if custom) | Customer Chat / Telegram Alert |

---

## 3. Error Handling & Fallback Protocols (`پروتکل مدیریت خطا و پایداری`)

1. **Legacy API Unreachable Protocol:**
   - If `Agent-LegacySync` fails to connect to `noghrehmashhad.ir` after 3 retries (exponential backoff: `2s, 8s, 30s`), it triggers an alert to Telegram (`[خطا: سامانه قدیمی نقره مشهد در دسترس نیست]`) and halts inventory modification to prevent accidental zero-stock overwrites.
2. **Silver Price Market Feed Outage:**
   - If `Agent-Pricing` cannot fetch the daily silver gram rate from primary API, it queries secondary backup API. If both fail, it notifies the owner via Telegram (`[خطا: دریافت قیمت روز نقره ناموفق بود - لطفاً قیمت را دستی وارد کنید: /price]`).
3. **Circuit Breaker Pattern:**
   - Any agent encountering 5 consecutive HTTP 500 errors from WooCommerce REST API automatically opens its circuit breaker for 30 minutes and notifies the owner via Telegram.
