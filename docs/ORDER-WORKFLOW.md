# گردش کار سفارشات و تأیید انسانی (`ORDER-WORKFLOW.md`)

This document details the order lifecycle states, Telegram interactive verification buttons, and out-of-stock exception workflows for **RADMAN SILVER STORE**.

---

## 1. Order Lifecycle States (`چرخه حیات سفارش`)

```text
[ Checkout Placed ] ──> [ Pending Payment ] ──(Zarinpal Success)──> [ On-Hold / Telegram Review ]
                                                                             │
                                                                   (Owner Click: [تأیید ارسال])
                                                                             │
                                                                             v
[ Customer SMS: Delivered ] <── [ Completed ] <──(Courier Track Code)── [ Processing ]
```

---

## 2. Telegram Interactive Approval Flow (`گردش کار تأیید تلگرامی`)

1. **Order Creation:** Customer completes checkout on `radmansilver.ir` via Zarinpal payment gateway.
2. **State Hold:** WooCommerce sets order status to **On-Hold (`در انتظار بررسی`)** and fires `order.created` webhook.
3. **Telegram Alert:** `Agent-OrderApproval` formats and sends message to owner:
   ```text
   📦 سفارش جدید #1052 تأیید پرداخت شد!
   مشتری: سارا احمدی | تلفن: 09120000000
   آدرس: تهران، خیابان ولیعصر...
   اقلام سفارش:
   - 1x RAD-RNG-W-1045 (انگشتر نقره مینیمال) | سایز: 54
   مبلغ کل پرداخت‌شده: ۲,۴۹۰,۰۰۰ تومان
   
   [تأیید موجودی و ارسال]     [عدم موجودی و لغو سفارش]
   ```
4. **Human Confirmation:**
   - **If Owner Clicks `[تأیید موجودی و ارسال]`:**
     - Order status transitions to **Processing (`در حال پردازش`)**.
     - Kavenegar SMS broadcast to customer: *«سفارش #1052 شما در رادمان سیلور تأیید شد و در حال آماده‌سازی برای ارسال است.»*
   - **If Owner Clicks `[عدم موجودی و لغو سفارش]`:**
     - Order status transitions to **Cancelled / Refund Required (`لغو شده`)**.
     - Urgent alert sent to accounting Telegram chat to process instant Shetab card refund within 2 hours.
     - Apology SMS sent to customer with 15% discount voucher for next order.
