# مستندات ربات تلگرام مدیریت فروشگاه (`TELEGRAM-BOT.md`)

This document details the webhook architecture, command whitelist, interactive menu structure, and the **Daily Pricing Preview Workflow** for `@RadmanSilverStoreBot`.

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
