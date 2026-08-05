# سیستم پشتیبانی مشتریان و پاسخگویی ۲۴ ساعته (`SUPPORT-SYSTEM.md`)

This document outlines the rule-based FAQ chatbot engine and immediate Telegram human escalation protocol for customer consultation on `radmansilver.ir`.

---

## 1. Rule-Based FAQ Chatbot Engine (`پاسخگوی خودکار سوالات متداول`)

The storefront widget (`Agent-Support`) provides instant 24/7 answers to standard customer questions:
- **Ring Sizing Guidance (`راهنمای تعیین سایز انگشتر`):** Displays interactive ring sizing table and measurement tutorial video.
- **Silver Maintenance (`روش نگهداری و تمیزکردن نقره`):** Instructions on polishing 925 sterling silver with the included RADMAN microfiber polishing cloth.
- **Shipping & Delivery (`ارسال و تحویل`):** Explains express courier shipping (`تیپاکس` Tipax and `پست پیشتاز` Post) delivery timelines (24h Tehran, 48-72h provincial).

---

## 2. Telegram Human Escalation Protocol (`ارجاع به پشتیبان انسانی در تلگرام`)

1. If a customer asks a custom question (e.g., *«آیا امکان ساخت این انگشتر با سایز ۶۴ یا نگین عقیق یمنی وجود دارد؟»*), `Agent-Support` immediately triggers an escalation alert to the owner's Telegram Support Group:
   ```text
   💬 درخواست مشاوره زنده از سایت!
   مشتری: مریم قاسمی | تلفن: 09121111111
   سوال: امکان ساخت انگشتر کد 1045 با نگین عقیق یمنی هست؟
   
   [پاسخ مستقیم در تلگرام به مشتری]
   ```
2. When the owner types a reply in Telegram, the message is routed back instantly to the customer's web chat session.
