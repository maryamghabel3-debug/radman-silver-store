# مستندات ربات تلگرام مدیریت فروشگاه (`TELEGRAM-BOT.md`)

This document details the webhook architecture, command whitelist, and interactive menu structure for the store management bot `@RadmanSilverStoreBot`.

---

## 1. Bot Architecture & Authorization Whitelist (`معماری و دسترسی‌ها`)

- **Webhook HTTPS Endpoint:** `https://radmansilver.ir/api/telegram-webhook`
- **Owner Admin Whitelist:** Commands are executed ONLY if the sender's Telegram User ID matches an ID declared in `TELEGRAM_ADMIN_IDS` in `.env`.
- **Unauthorized Handling:** Any request from an unauthorized Telegram ID receives zero response and logs a security warning.

---

## 2. Interactive Slash Command Structure (`فرمان‌های کنترلی ربات`)

| Command | Purpose | Interactive Response / Action |
| :--- | :--- | :--- |
| **`/status`** | Store Health Check | Returns today's sales total, pending orders count, and last sync timestamp |
| **`/price`** | Silver Rate Override | Triggers interactive prompt to confirm or manually adjust today's 925 silver gram rate |
| **`/orders`** | Order Approval Queue | Displays list of `On-Hold` orders waiting for fulfillment button click |
| **`/sync_now`** | Force Legacy Sync | Immediately runs `Agent-LegacySync` against `noghrehmashhad.ir` |
| **`/help`** | Admin Reference | Lists all available management commands |
