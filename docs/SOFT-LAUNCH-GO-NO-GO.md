# سند تصمیم‌گیری مدیریتی و ارزیابی آمادگی لانچ نرم (`SOFT-LAUNCH-GO-NO-GO.md`)

> **ماتریس تصمیم‌گیری مدیریتی برای راه‌اندازی آزمایشی رادمان سیلور (RADMAN Soft Launch Go / No-Go Decision Sheet)**  
> *این سند به عنوان ابزار ممیزی نهایی برای تصمیم‌گیری ورود به مرحله «لانچ نرم» با گروه کاربران آزمایشی VIP (`RADMAN-VIP15` Cohort) استفاده می‌شود.*

> **راهنمای وضعیت‌های چک‌لیست (Status Definitions):**  
> - **`CONFIRMED`**: تأییدشده و نهایی  
> - **`PENDING VENDOR ANSWER`**: در انتظار پاسخ فنی پشتیبانی هاستینگ (میزبان‌فا / پارس‌پک)  
> - **`PENDING OWNER DECISION`**: در انتظار تصمیم یا تأیید مالک برند  
> - **`NOT YET TESTED`**: هنوز تست نشده (آماده برای تست در استیجینگ/پروداکشن)  
> - **`NOT APPLICABLE`**: غیرقابل اعمال / بلاموضوع  

---

## 1. Readiness Audit Categories (`حوزه‌های ارزیابی آمادگی`)

### A. Business Readiness (`آمادگی کسب‌وکار`)
- [ ] CONFIRMED : تأیید و قفل نهایی هویت بصری، لوگوی مینیمال هدر (`Primary T0`) و لوگوی بسته‌بندی (`Tagline T2`).
- [ ] CONFIRMED : تأیید قوانین ۴ گانه قیمت‌گذاری و ورود نرخ روز نقره از تلگرام (`/price 85000`).
- [ ] CONFIRMED : تأیید اصل انبار دقیق ۱ به ۱ (`stock=1` قابل فروش است، بدون بافر ریاضی).

### B. Technical & Infrastructure Readiness (`آمادگی فنی و زیرساخت`)
- [ ] Pending : پایداری سرور میزبان داخل ایران (`MizbanFa Mars Plan` — تک‌سرور موقت برای ماه جاری، صرفاً RADMAN؛ ارزیابی مجدد ماه بعد / `Status: APPROVED TEMPORARILY — CURRENT MONTH`).
- [ ] Pending : صحت نصب وردپرس ۶.x، ووکامرس و قالب Blocksy Child Theme (`Status: NOT YET TESTED`).
- [ ] Pending : صحت عملکرد وب‌سرویس ووکامرس (`WooCommerce REST API v3`) و وب‌هوک‌های خروجی (`Status: NOT YET TESTED`).

### C. Catalog & Content Readiness (`آمادگی کاتالوگ و محتوا`)
- [ ] Pending : ورود و انتشار آزمایشی حداقل ۵۰ محصول نقره ۹۲۵ با مشخصات کامل (وزن، عیار، سایز و نگین).
- [ ] Pending : صحت کیفیت تصاویر گالری محصولات (مربع ۱:۱ WebP زیر ۲۰۰ کیلوبایت با واترمارک ۱۵٪).
- [ ] Pending : در دسترس بودن تمامی ۱۱ صفحه استاتیک فارسی (درباره ما، تماس با ما، حریم خصوصی، قوانین خرید، سوالات متداول، راهنمای سایز و...).

### D. Payment & Fulfillment Readiness (`آمادگی پرداخت و لجستیک`)
- [ ] Pending : صحت کارکرد درگاه پرداخت زرین‌پال در محیط زنده و بازگشت موفق به صفحه رسید ووکامرس (`Status: NOT YET TESTED`).
- [ ] Pending : آماده بودن بسته‌بندی‌های لوکس رادمان سیلور، جعبه هدیه، دستمال پولیش و فاکتور اصالت.

### E. Messaging & Hybrid HITL Readiness (`آمادگی اطلاع‌رسانی و تأیید ترکیبی`)
- [ ] Pending : صحت ارسال پیامک‌های کاوه‌نگار به مشتری و مالک (کد OTP، هشدار ثبت سفارش جدید به مالک، تأیید سفارش و کد رهگیری مرسوله) — **الزام حیاتی لانچ (`Mandatory SMS Path`)**.
- [ ] Pending : صحت عملکرد ربات تلگرام مدیریت (`[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`) برای دریافت دستور `/price`، نمایش پیش‌نمایش قیمت و کارکرد دکمه‌های `[تأیید موجودی و ارسال]` و `[عدم موجودی و لغو]` (`Status: NOT YET TESTED` — **کانال اختیاری و ترجیحی / `Optional Preferred Channel`**).
- [ ] Pending : تست و تأیید مسیر جایگزین تأیید سفارش توسط مالک از طریق پنل مدیریت ووکامرس در مواقع عدم دسترسی به تلگرام (`WooCommerce Admin HITL Fallback Tested`).

### F. Security & Support Readiness (`آمادگی امنیتی و پشتیبانی`)
- [ ] Pending : فعال بودن فایروال Wordfence و تأیید جداسازی کامل اسرار و کلیدها در `.env`.
- [ ] Pending : زمان‌بندی بک‌آپ روزانه دیتابیس در UpdraftPlus و تست بازیابی (`Status: TBD / PENDING`).
- [ ] Pending : فعال بودن پاسخگوی متداول پشتیبانی سایت و پروتکل ارجاع فوری به کارشناس در تلگرام.

---

## 2. Critical Blockers (`موانع بحرانی و خطوط قرمز لانچ`)

> ⚠️ **الزام اکید اجرایی:** در صورت وجود حتی **یک مورد** از موانع بحرانی زیر در وضعیت حل‌نشده، ورود به مرحله لانچ نرم **کاملاً ممنوع (NO-GO)** است:

1. **عدم تأیید تراکنش زنده یا شکست Callback درگاه پرداخت زرین‌پال (`Payment Callback Not Verified`).**
2. **اختلال همزمان در اطلاع‌رسانی پیامکی مالک و عدم کارکرد مسیر جایگزین تأیید سفارش در پنل مدیریت ووکامرس (`Both Owner Notification & WooCommerce Admin HITL Fallback Failed`).** *(توجه: عدم دسترسی به تلگرام به تنهایی مانع لانچ نیست؛ پیامک مسیر الزامی و تلگرام کانال اختیاری است).*
3. **عدم اطمینان از صحت انطباق ۱:۱ موجودی انبار و ثبت سفارش در ووکامرس (`Inventory Sync Uncertain`).**
4. **تست‌نشده بودن فرآیند بازیابی بک‌آپ دیتابیس در صورت بروز فاجعه (`Backup Restore Untested`).**
5. **نامعتبر بودن یا خطای گواهینامه امنیتی SSL (`SSL Invalid / TLS Certificate Error`).**
6. **ایندکس شدن ناخواسته محیط استیجینگ در گوگل (`Staging Accidentally Indexable by Search Engines`).**

---

## 3. Nice-to-Have Items (`موارد ترجیحی برای فازهای بعد`)

- [ ] Pending : اتصال سیستم توصیه‌گر هوشمند محصولات مرتبط در صفحه محصول.
- [ ] Pending : راه‌اندازی کمپین‌های تبلیغاتی پولی در ترب و ایمالز (مربوط به فاز ۶ عمومی).
- [ ] Pending : تولید خودکار محتوای سئو با هوش مصنوعی مولد (به تعویق افتاده تا رشد درآمد).

---

## 4. Final Managerial Decision Box (`جعبه تصمیم‌گیری نهایی مدیریتی`)

```text
+-------------------------------------------------------------------------------+
|                      FINAL SOFT LAUNCH DECISION                               |
|                                                                               |
|            [   ] GO  (تأیید ورود به مرحله لانچ نرم با کاربران VIP)          |
|            [   ] NO-GO  (توقف تا رفع کامل موانع بحرانی)                       |
|                                                                               |
|  Date of Audit: ____ / ____ / 2026        Target Launch Date: TBD / PENDING    |
+-------------------------------------------------------------------------------+
```

### Official Approval Lines (`امضاهای تأییدیه رسمی`)

| Role | Responsibility | Signature / Sign-Off | Date |
| :--- | :--- | :---: | :---: |
| **Brand Owner (`مالک برند`)** | Business, Pricing & Catalog Sign-Off | `PENDING APPROVAL` | `YYYY-MM-DD` |
| **Technical Lead (`مدیر فنی / معمار سیستم`)** | Infrastructure, Security & API Sign-Off | `PENDING APPROVAL` | `YYYY-MM-DD` |
| **Operations Lead (`مدیر اجرایی و لجستیک`)** | Order Workflow, SMS & Fulfillment Sign-Off | `PENDING APPROVAL` | `YYYY-MM-DD` |
