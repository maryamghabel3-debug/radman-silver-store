# گردش کار سفارشات و تأیید انسانی (`ORDER-WORKFLOW.md`)

This document details the order lifecycle states, hybrid SMS/Telegram notification model, human-in-the-loop (`HITL`) verification paths, and out-of-stock exception workflows for **RADMAN SILVER 925**.

---

## 1. Hybrid Owner Notification & Approval Model (`مدل ترکیبی اطلاع‌رسانی و تأیید سفارش`)

To guarantee business continuity during international internet disruptions or connectivity issues, RADMAN SILVER 925 operates under a resilient **Hybrid Notification & Approval Workflow**:
- **Primary Mandatory Channel (`SMS via Kavenegar`):** SMS is the mandatory primary notification channel. Every new paid order immediately triggers an SMS alert to the brand owner. Launch and operations require a functional SMS notification path.
- **Secondary Optional Channel (`Telegram Bot`):** Telegram is an optional secondary convenience channel. When reachable, it provides instant interactive approval buttons (`[تأیید موجودی و ارسال]` / `[عدم موجودی و لغو]`). However, **Telegram is NOT the sole business-critical approval mechanism**, and operations/launch are never blocked solely because Telegram is unavailable.
- **Mandatory Human-in-the-Loop (`HITL`) Governance:** Every paid order requires human verification of physical inventory before dispatch (`1:1 stock reality`). Human approval remains mandatory across all channels.

---

## 2. Order Lifecycle States (`چرخه حیات سفارش`)

```text
[ Checkout Placed ] ──> [ Pending Payment ] ──(Zarinpal Success)──> [ On-Hold / Pending Human Review ]
                                                                             │
                                              +------------------------------+------------------------------+
                                              │                                                             │
                                              v                                                             v
                                [ Path A: Telegram Available ]                                [ Path B: Telegram Unreachable ]
                                (Owner Button: [تأیید ارسال])                                 (WooCommerce Admin Manual Status)
                                              │                                                             │
                                              +------------------------------+------------------------------+
                                                                             │
                                                                             v
[ Customer SMS: Delivered ] <── [ Completed ] <──(Courier Track Code)── [ Processing ]
```

---

## 3. Human Order Approval Paths (`مسیرهای تأیید انسانی سفارش`)

1. **Order Placement:** Customer completes checkout on `radmansilver.ir` via Zarinpal payment gateway.
2. **State Hold:** WooCommerce sets order status to **On-Hold (`در انتظار بررسی`)** and triggers notifications.
3. **Owner Notifications:**
   - **Mandatory SMS Alert:** Owner receives an immediate SMS notification via Kavenegar containing order ID and total amount.
   - **Optional Telegram Alert:** If Telegram is reachable, `Agent-OrderApproval` sends an interactive message to the owner:
     ```text
     📦 سفارش جدید #1052 تأیید پرداخت شد!
     مشتری: سارا احمدی | تلفن: 09120000000
     آدرس: تهران، خیابان ولیعصر...
     اقلام سفارش:
     - 1x RAD-RNG-W-1045 (انگشتر نقره مینیمال) | سایز: 54
     مبلغ کل پرداخت‌شده: ۲,۴۹۰,۰۰۰ تومان
     
     [تأیید موجودی و ارسال]     [عدم موجودی و لغو سفارش]
     ```

4. **Two Official Human Approval Paths:**
   - **Approval Path A (Telegram Convenience Channel — When Available):**
     - **If Owner Clicks `[تأیید موجودی و ارسال]`:**
       - Order status transitions to **Processing (`در حال پردازش`)**.
       - Kavenegar SMS broadcast to customer: *«سفارش #1052 شما در رادمان سیلور تأیید شد و در حال آماده‌سازی برای ارسال است.»*
     - **If Owner Clicks `[عدم موجودی و لغو سفارش]`:**
       - Order status transitions to **Cancelled / Refund Required (`لغو شده`)**.
       - Urgent alert sent to accounting to process instant Shetab card refund within 2 hours.
       - Apology SMS sent to customer with 15% discount voucher for next order.
   - **Approval Path B (WooCommerce Admin Fallback — When Telegram is Unreachable):**
     - **If Telegram is unreachable or offline:**
       - Owner logs directly into the **WooCommerce Admin Panel** on the Iranian server (`radmansilver.ir/wp-admin`).
       - Owner manually inspects order `#1052` and changes order status from **On-Hold (`در انتظار بررسی`)** to **Processing (`در حال پردازش`)** (approved) or **Cancelled (`لغو شده`)** (rejected).
       - Automation agents observe the order status change in WooCommerce and automatically fire the corresponding Kavenegar SMS notification to the customer (confirmation SMS for approved orders, or refund/voucher SMS for rejected orders).
       - This SMS-only fallback path ensures 100% business continuity without depending on international messaging platforms.
