# چک‌لیست انتقال به محیط پروداکشن و لایو (`PRODUCTION-CUTOVER-CHECKLIST.md`)

> **راهنمای اجرایی انتقال از استیجینگ به دامنه اصلی (Production Cutover & Go-Live Checklist)**  
> *این چک‌لیست گام‌های حساس انتقال فروشگاه رادمان سیلور به دامنه اصلی (`radmansilver.ir`) را پس از تأیید نهایی محیط استیجینگ مشخص می‌کند.*

> **راهنمای وضعیت‌های چک‌لیست (Status Definitions):**  
> - **`CONFIRMED`**: تأییدشده و نهایی  
> - **`PENDING VENDOR ANSWER`**: در انتظار پاسخ فنی پشتیبانی هاستینگ (میزبان‌فا / پارس‌پک)  
> - **`PENDING OWNER DECISION`**: در انتظار تصمیم یا تأیید مالک برند  
> - **`NOT YET TESTED`**: هنوز تست نشده (آماده برای تست در استیجینگ/پروداکشن)  
> - **`NOT APPLICABLE`**: غیرقابل اعمال / بلاموضوع  

---

## 1. Domain & DNS Cutover (`تغییر رکوردهای DNS و دامنه اصلی`)

- [ ] Pending : تنظیم رکوردهای `A Record` و `CNAME` دامنه اصلی (`radmansilver.ir`) به IP سرور پروداکشن (`[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`).
- [ ] Pending : بررسی و تأیید ریدایرکت ۳۰۱ دائمی از دامنه ثانویه (`radman925.ir`) به دامنه اصلی (`radmansilver.ir`).
- [ ] Pending : بررسی و تنظیم ریدایرکت خودکار از `http://` به `https://` و از `www` به بدون `www` (یا بالعکس طبق استاندارد سئو).

---

## 2. SSL & Edge Security (`گواهینامه SSL و تنظیمات CDN/WAF`)

- [ ] Pending : بررسی اعتبار و صحت نصب گواهینامه SSL روی دامنه اصلی (`radmansilver.ir`).
- [ ] Pending : پیکربندی شبکه توزیع محتوا و فایروال لبه (`Cloudflare` or `ArvanCloud` — وضعیت: `PENDING OWNER DECISION` بر اساس ارزیابی جایگزین‌ها؛ استفاده همزمان الزامی نیست).
- [ ] Pending : تنظیم قوانین کش لبه (`Cache Rules`):
  - کش کامل صفحات عمومی و گالری محصولات.
  - **Bypass کامل کش** برای صفحات سبد خرید (`/cart/`)، پرداخت (`/checkout/`)، حساب کاربری (`/my-account/`) و مسیرهای REST API (`/wp-json/wc/v3/`).

---

## 3. Production Security & Hardening (`مقاوم‌سازی امنیتی پروداکشن`)

- [ ] Pending : فعال‌سازی حالت پروداکشن در وردپرس (`define('WP_DEBUG', false);`).
- [ ] Pending : تنظیم دسترسی فایل‌ها (`chmod 755` برای پوشه‌ها و `chmod 644` برای فایل‌ها؛ `chmod 600` برای `wp-config.php` و `.env`).
- [ ] Pending : بررسی فعال بودن فایروال Wordfence در حالت Full Enforcement و محدودسازی تلاش‌های ورود ناموفق.

---

## 4. Live Gateway & Messaging Verification (`تأیید درگاه‌های پرداخت و اطلاع‌رسانی`)

- [ ] Pending : **Payment Gateway Live Verification:** خروج درگاه **زرین‌پال (`Zarinpal`)** از حالت سندباکس و ثبت Merchant ID واقعی در `.env`. انجام یک تراکنش واقعی با مبلغ کم تاییدشده توسط مالک در زمان تست (a low-value live transaction amount approved by the owner at test time) با کارت بانکی عضو شتاب و بررسی صحت بازگشت به سایت (`Callback Verification`).
- [ ] Pending : **SMS Gateway Verification:** اتصال کلید زنده **کاوه‌نگار (`Kavenegar`)** و تست ارسال پیامک OTP ورود و پیامک موفقیت سفارش.
- [ ] Pending : **Telegram HITL Flow Verification:** تست ارسال وب‌هوک سفارش جدید به ربات تلگرام (`[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`) و بررسی عملکرد دکمه‌های تعاملی `[تأیید موجودی و ارسال]` و `[عدم موجودی و لغو]`.

---

## 5. Search Engine Indexing & Analytics (`قوانین ایندکس و ابزارهای تحلیل`)

- [ ] Pending : **حذف `noindex` و باز کردن دسترسی موتورهای جستجو:** تنظیم گزینه *«اجازه به موتورهای جستجو برای بررسی سایت»* در وردپرس و تأیید تولید صحیح `sitemap_index.xml` توسط RankMath.
- [ ] Pending : ثبت آدرس فروشگاه در **Google Search Console** و ارسال نقشه سایت (`Status: TBD / PENDING`).
- [ ] Pending : اتصال **Google Analytics 4 (GA4)** جهت رهگیری ترافیک و رویدادهای خرید ووکامرس (`Status: TBD / PENDING`).

---

## 6. Pre-Launch Backup Snapshot & Rollback Plan (`بک‌آپ قبل از لانچ و برنامه استرداد`)

- [ ] Pending : **Pre-Launch Snapshot:** تهیه یک نسخه پشتیبان کامل از دیتابیس و فایل‌ها پیش از عمومی شدن سایت و ذخیره در فضای ابری آفلاین (`ArvanCloud` or `S3` — alternatives under evaluation).
- **Rollback Plan (`برنامه بازگشت سریع در صورت بروز بحران`):**
  - در صورت بروز خطای بحرانی در درگاه پرداخت یا دیتابیس هنگام لانچ، ترافیک دامنه از طریق DNS/CDN موقتاً به صفحه انتظار (`Maintenance Page`) هدایت شده و دیتابیس از روی آخرین اسنپ‌شات سالم UpdraftPlus بازگردانی می‌شود.

---

## 7. Production Cutover Sign-Off Table (`جدول تأییدیه نهایی انتقال به پروداکشن`)

| Item | Owner | Status | Notes |
| :--- | :---: | :---: | :--- |
| **DNS Cutover & radman925.ir Redirect** | Technical Lead / DNS Admin | `NOT YET TESTED` | 301 canonical redirect to radmansilver.ir |
| **SSL & Edge Cache Bypass Rules** | DevOps Lead | `NOT YET TESTED` | Bypass cache on /checkout, /cart, /wp-json |
| **Zarinpal Live Payment & Callback Test**| E-Commerce Developer | `NOT YET TESTED` | Perform real low-value Shetab debit card transaction |
| **Kavenegar SMS & Telegram HITL Verification** | Automation Agent Lead | `NOT YET TESTED` | Verify interactive Telegram approval buttons |
| **Search Engine Indexing & GA4/GSC** | SEO Strategist | `NOT YET TESTED` | Enable indexing, submit sitemap.xml |
| **Pre-Launch Snapshot & Rollback Audit** | Security / DevOps Lead | `NOT YET TESTED` | Verify offline backup restoration procedure |
