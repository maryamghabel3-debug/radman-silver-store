# مستندات ربات تلگرام مدیریت فروشگاه (`TELEGRAM-BOT.md`)

This document details the webhook architecture, command whitelist, interactive menu structure, and the **Daily Pricing Preview Workflow** for `[RADMAN_TELEGRAM_BOT_USERNAME: TBD]` as an **optional operational convenience channel**.

---

## 1. Bot Architecture & Authorization Whitelist (`معماری و دسترسی‌ها`)

- **Webhook HTTPS Endpoint:** `https://radmansilver.ir/api/telegram-webhook`
- **Owner Admin Whitelist:** Commands are executed ONLY if the sender's Telegram User ID matches an ID declared in `TELEGRAM_ADMIN_IDS` in `.env`.

---

## 2. Interactive Slash Command Structure (`فرمان‌های کنترلی ربات`)

| Command | Purpose | Interactive Response / Action |
| :--- | :--- | :--- |
| **`/status`** | Store Health Check | Returns today's sales total, pending orders count, and last sync timestamp |
| **`/price [rate]`** | Daily Silver Rate Input | Triggers calculation preview for `silver_weight_only` and `silver_weight_plus_stone` items |
| **`/orders`** | Order Approval Queue | Displays list of `On-Hold` orders waiting for fulfillment button click |
| **`/sync_now`** | Force Legacy Sync | Immediately runs `Agent-LegacySync` against `noghrehmashhad.ir` Admin Panel API |

---

## 3. Daily Pricing Preview & Approval Flow (`گردش کار پیش‌نمایش قیمت‌گذاری`)

```text
[ Owner sends: /price 85000 ]
             │
             v
[ Agent-Pricing calculates new prices ]
             │
             v
[ Telegram Bot returns Preview Summary ]
  - Affected weight-only: 112
  - Affected weight+stone: 64
  - Skipped locked: 42
  - Skipped missing-data: 8
  - Top 20 Price Changes List
             │
      ┌──────┴────────────────────────────┐
      ▼                                   ▼
[ Click: تأیید و اعمال قیمت ]        [ Click: لغو عملیات ]
      │                                   │
      v                                   v
[ WooCommerce Batch Update ]       [ Zero Changes Made ]
```

---

## 4. Operational Role & Business Continuity Fallback (`نقش عملیاتی و جایگزین مواقع قطعی`)

- **Optional Operational Convenience Channel:** The Telegram bot (`[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`) serves as an optional operational convenience channel for daily rate input and interactive order approvals.
- **Not Sole Business-Critical Mechanism:** **Telegram is NOT the sole business-critical approval mechanism.** The platform is designed so that no order fulfillment or store operations are permanently blocked if Telegram becomes unreachable or filtered.
- **WooCommerce Admin Fallback:** If Telegram is unreachable, owner approval continues through the **WooCommerce Admin Panel** fallback path:
  1. For new order review, the owner logs into WooCommerce Admin (`radmansilver.ir/wp-admin`), checks pending `On-Hold` orders, and manually updates order status to `Processing` (approved) or `Cancelled` (rejected).
  2. Automation agents monitor WooCommerce order statuses directly and send mandatory SMS customer notifications via Kavenegar without requiring Telegram connectivity.
