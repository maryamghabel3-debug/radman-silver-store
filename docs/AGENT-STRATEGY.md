# استراتژی و معماری ایجنت‌های اتوماسیون (`AGENT-STRATEGY.md`)

This document defines the governance philosophy, event orchestration, and human-in-the-loop controls for the AI automation agents operating in **RADMAN SILVER 925**.

---

## 1. Executive Summary & Design Philosophy (`اصول حاکمیت هوش مصنوعی`)

The RADMAN SILVER automation ecosystem operates under a strict **Human-in-the-Loop (`HITL`) Governance Model**:
- **Pricing Governance:** The owner inputs a single daily rate (`نرخ امروز هر گرم نقره = X تومان`) via Telegram Bot. `Agent-Pricing` automatically applies `final_price = weight_grams * daily_rate (owner enters rate manually via Telegram)` for weight-based items.
- **Inventory & Fulfillment Governance:** `stock = 1` is completely normal and sellable (`1:1 mapping`). To prevent overselling from manual legacy inventory latency, every customer order requires **Human-in-the-Loop (`HITL`) Order Confirmation** (mandatory SMS primary alert + optional Telegram convenience channel, with WooCommerce Admin manual approval fallback) before dispatch.

---

## 2. Agent Ecosystem Responsibilities Table

| Agent Name | Core Mandate | Execution Trigger | Human Approval Required? | Output Target |
| :--- | :--- | :--- | :--- | :--- |
| **`Agent-LegacySync`** | Read-Only Admin API sync (Exact 1:1 stock: `1 -> 1`, `0 -> 0`) | Twice daily cron / `/sync_now` | **YES** (Creates Drafts only) | WooCommerce DB (`Drafts`) |
| **`Agent-Pricing`** | Simple Daily Rate calculation (`final_final_price = weight_grams * daily_rate (owner enters rate manually via Telegram)`) | On owner Telegram command `/price` | **YES** (Owner inputs daily rate) | WooCommerce Product Prices |
| **`Agent-OrderApproval`** | Hybrid SMS/Telegram order alert & HITL verification before shipping | Instant upon checkout | **YES** (Telegram buttons or WooCommerce Admin fallback) | WooCommerce Order Status & SMS Alerts |
| **`Agent-Media`** | Crop 1:1, convert WebP & apply subtle watermark | On new draft creation | **NO** (Automated processing) | WordPress Media Library |
| **`Agent-Support`** | Answer standard sizing/care FAQ via rule engine | On user chat message | **NO** (Escalates to human if custom) | Customer Chat / Telegram Alert |
