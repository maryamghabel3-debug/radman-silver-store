# راهنمای اجرایی و چک‌لیست راه‌اندازی پس از خرید هاست (`POST-PURCHASE-SETUP-RUNBOOK.md`)

> **راهنمای عملیاتی گام‌به‌گام برای مدیر سیستم پس از خرید هاست میزبان‌فا (MizbanFa Mars Post-Purchase Runbook)**  
> *این راهنما به عنوان چک‌لیست اجرایی برای استقرار فروشگاه **رادمان سیلور (`RADMAN SILVER 925`)** بر روی پلن مارس میزبان‌فا تدوین شده است.*

---

## 0. وضعیت تصمیم‌گیری هاستینگ و مشخصات مصوب (Approved Temporary Decision)

- **Official Status (وضعیت رسمی):** **`APPROVED FOR INITIAL ONE-MONTH PURCHASE AND STAGING TRIAL — NOT YET PURCHASED`** (مجوز خرید اولیه برای دوره یک‌ماهه آزمایشی استیجینگ صادر شده است اما هنوز خریداری نشده است / `approved to purchase, but not yet purchased`).
- **Hosting Vendor (فروشنده):** **MizbanFa** (`میزبان‌فا` - سرویس هاست وردپرس/ووکامرس ایران)
- **Selected Plan:** **Mars** (`مارس` — 60 GB NVMe Disk, advertised 12 Cores / 12 GHz Equivalent CPU, advertised 12 GB RAM, cPanel)
- **Scope limitation:** **`RADMAN SILVER ONLY`** — این سرویس منحصراً به برند رادمان سیلور اختصاص دارد.
- **RIDELIN Scope Rule:** **RIDELIN must not be installed or deployed on this host.** (هیچ‌گونه استقراری برای رایدلین روی این هاست انجام نخواهد شد).
- **Architecture & Agent Co-Location:** Storefront hosting on MizbanFa Mars is approved for the initial trial. Co-locating Python agents on the same host is **`CONDITIONAL — pending post-purchase Python/Cron/outbound connectivity acceptance tests.`** Python agents may be deployed on the same host only after real verification of Python, pip, venv, Cron runtime, outbound HTTPS, filesystem permissions, process limits, and Legacy API connectivity. If those checks fail during the refund/test window, agents must be moved to a separate runner without blocking the WooCommerce storefront.
- **Review Deadline (مهلت بررسی مجدد):** **Review within 30 days after the actual provisioning date and before production launch, whichever occurs first. Provisioning date: TBD.**
- **Owner Notification Model:** SMS via Kavenegar is mandatory. Telegram is optional. WooCommerce Admin is the fallback HITL approval path. Telegram availability must not be a single point of failure (`SMS mandatory, Telegram optional, WooCommerce Admin fallback allowed`).
- **Cache Policy:** **`LiteSpeed Cache active, WP Rocket inactive, Redis conditional.`** (LiteSpeed Cache is the selected project page-cache plugin; LiteSpeed Cache and WP Rocket must not be activated simultaneously. Redis persistent object cache may only be activated after real connectivity verification. Distinguish vendor-provided features from project-approved active configuration).
- **Yellow Flag (ریسک نسخه دیتابیس):** نسخه گزارش‌شده از پشتیبانی فروشنده `MariaDB 10.3.39` است. وضعیت: **`STAGING-ONLY TEMPORARY COMPATIBILITY WAIVER; production acceptance pending.`** (اقدام: بررسی نسخه واقعی پس از خرید و درخواست ارتقا از پشتیبانی در صورت لزوم. Go/No-Go پروداکشن تا زمان بررسی سازگاری و امنیت دیتابیس مسدود است).
- **Refund/Test Window:** Vendor support stated up to 14 days after purchase. **`TO BE RECONFIRMED AGAINST THE PURCHASE TERMS AT CHECKOUT.`** (این مورد شرط تضمین حقوقی بدون قید و شرط تلقی نمی‌شود).
- **Canonical Safe Staging Toolkit:** برای اجرای ابزار استقرار ایمن استیجینگ به سند رسمی [docs/WORDPRESS-INSTALLATION-MARS-RUNBOOK.md](WORDPRESS-INSTALLATION-MARS-RUNBOOK.md) مراجعه کنید.
- **Future Explicit Mission Requirement:** اجرای واقعی روی سرور نیازمند صدور مأموریت مستقل مصوب در آینده است.
- **Prohibit Secrets Inside Web Root:** نگهداری فایل اسرار `.env` داخل پوشه‌های عمومی ریشه وب (`public_html` یا دایرکتوری استیجینگ) اکیداً ممنوع است و باید در مسیر خصوصی حساب کاربری خارج از ریشه وب قرار گیرد.
- **Prohibit Production Installation in Initial Execution Mission:** استقرار پروداکشن در مأموریت اولیه اجرا اکیداً ممنوع است؛ استقرار روی استیجینگ باید انجام و تست‌های تضمین کیفیت (QA) تأیید شوند.

---

## A. Immediately After Purchase (`اقدامات بلافاصله پس از خرید`)

- [ ] PENDING : **Login to hosting panel:** ورود به پنل کاربری میزبان‌فا و بررسی دسترسی کامل به سرویس خریداری‌شده.
- [ ] PENDING : **Enable 2FA if available:** فعال‌سازی احراز هویت دو مرحله‌ای (`2FA`) برای اکانت هاستینگ جهت امنیت حداکثری.
- [ ] PENDING : **Note cPanel URL:** یادداشت آدرس دقیق ورود به پنل `cPanel` و ذخیره امن نام کاربری و رمز عبور (منحصراً در ابزار مدیریت پسورد).
- [ ] PENDING : **Note Nameservers / DNS panel access:** یادداشت نیم‌سرورهای میزبان‌فا (`NS Records`) و دسترسی به پنل مدیریت دامنه/DNS.
- [ ] PENDING : **Verify SSL tools:** بررسی در دسترس بودن ابزارهای صدور خودکار گواهینامه امنیتی (`Let's Encrypt / AutoSSL`).
- [ ] PENDING : **Verify Terminal/Shell Access availability:** بررسی و تست ورود به محیط ترمینال (`Terminal / SSH`) در cPanel برای اجرای اسکریپت‌های پایتون.
- [ ] PENDING : **Verify PHP selector:** بررسی تنظیمات PHP Selector و اطمینان از امکان انتخاب نسخه `PHP 8.2` یا `8.3` و فعال‌سازی اکستنشن‌های ضروری (`mbstring`, `cURL`, `imagick`, `bcmath`, `intl`).
- [ ] PENDING : **Verify Cron:** بررسی ابزار `Cron Jobs` در cPanel برای زمان‌بندی اجرای ایجنت‌های همگام‌سازی و اسکریپت‌ها.
- [ ] PENDING : **Verify Backup tools:** بررسی در دسترس بودن ابزار بک‌آپ‌گیری cPanel و تنظیمات JetBackup / زمان‌بندی پشتیبان‌گیری روزانه.

---

## B. Create Staging (`ایجاد محیط استیجینگ`)

- [ ] PENDING : **Create subdomain:** ایجاد ساب‌دامنه استیجینگ به آدرس `[PROPOSED: staging.radmansilver.ir — final DNS TBD]`.
- [ ] PENDING : **Separate document root:** اختصاص یک مسیر پوشه مستقل و ایزوله (`Document Root`) برای استیجینگ مجزا از مسیر اصلی `public_html`.
- [ ] PENDING : **Separate database:** ساخت یک دیتابیس و نام کاربری مجزای MySQL/MariaDB برای استیجینگ (ایزوله از پروداکشن).
- [ ] PENDING : **Force noindex:** اعمال اکید `X-Robots-Tag: noindex, nofollow` و فعال‌سازی گزینه *«از موتورهای جستجو درخواست کن تا این وب‌سایت را بررسی نکنند»* در تنظیمات وردپرس استیجینگ.
- [ ] PENDING : **Basic auth if possible:** فعال‌سازی احراز هویت اولیه (`HTTP Basic Authentication` با `.htpasswd`) روی پوشه استیجینگ در صورت امکان جهت ممانعت از دسترسی عمومی.

---

## C. Create Production Database Objects (`ایجاد پایگاه داده پروداکشن - موکول‌شده به بعد از استیجینگ`)

- [ ] PENDING : **DB name placeholder:** ایجاد پایگاه داده پروداکشن (`RADMAN_PROD_DB_NAME_PLACEHOLDER`) پس از تأیید استیجینگ.
- [ ] PENDING : **DB user placeholder:** ایجاد کاربر مستقل پایگاه داده با رمز عبور قدرتمند (`RADMAN_PROD_DB_USER_PLACEHOLDER`).
- [ ] PENDING : **Charset/Collation target:** تنظیم دقیق Collation پایگاه داده روی **`utf8mb4_unicode_ci`** (و بررسی نسخه واقعی MariaDB/MySQL سرور پس از ساخت).

---

## D. WordPress Installation Order (`ترتیب نصب وردپرس و افزونه‌ها در استیجینگ`)

> *برای نصب خودکار با `WP-CLI` به سند [docs/WORDPRESS-INSTALLATION-MARS-RUNBOOK.md](WORDPRESS-INSTALLATION-MARS-RUNBOOK.md) مراجعه کنید.*

- [ ] PENDING : **1. WordPress:** نصب هسته وردپرس نسخه ۶.x فارسی/انگلیسی با منطقه زمانی `Asia/Tehran`.
- [ ] PENDING : **2. WooCommerce:** نصب و راه‌اندازی افزونه فروشگاه‌ساز ووکامرس (تنظیم واحد پول روی **IRR / ریال** طبق دروازه امنیتی واحد پول و عدم اعشار).
- [ ] PENDING : **3. Persian WooCommerce:** نصب افزونه «ووکامرس فارسی» جهت تقویم جلالی، شهرهای ایران و نمایش صحیح واحد پول.
- [ ] PENDING : **4. Blocksy + companion:** نصب قالب مینیمال Blocksy و افزونه مکمل (`blocksy-companion`). استقرار قالب فرزند (`Child Theme`) در وضعیت PENDING است.
- [ ] PENDING : **5. RankMath SEO:** نصب افزونه سئو با اسلاگ رسمی `seo-by-rank-math` (بدون Yoast).
- [ ] PENDING : **6. Wordfence Security:** نصب و فعال‌سازی افزونه امنیتی `wordfence`.
- [ ] PENDING : **7. UpdraftPlus Backup:** نصب افزونه `updraftplus` جهت پشتیبان‌گیری.
- [ ] PENDING : **8. LiteSpeed Cache & Redis:** نصب افزونه کش `litespeed-cache` (`WP Rocket` غیرفعال است) و فعال‌سازی `redis-cache` منوط به موفقیت تست ارتباط Redis.
- [ ] PENDING : **9. Payment / SMS integrations:** درگاه پرداخت زرین‌پال و پیامک کاوه‌نگار (در وضعیت PENDING بررسی بسته مصوب).

---

## E. Security Baseline (`اعمال خطوط قرمز امنیتی`)

- [ ] PENDING : **Strong admin username:** انتخاب نام کاربری غیرقابل حدس برای مدیر وردپرس (ممنوعیت اکید استفاده از `admin` یا `radman`).
- [ ] PENDING : **Limit login:** محدودسازی تلاش‌های ورود ناموفق (`Login Attempt Limit`) توسط Wordfence.
- [ ] PENDING : **Disable file edit if appropriate:** غیرفعال‌سازی ویرایشگر قالب و افزونه در پیشخوان وردپرس با درج `define('DISALLOW_FILE_EDIT', true);` در `wp-config.php`.
- [ ] PENDING : **Separate secrets outside web root:** نگهداری تمامی کلیدهای وب‌سرویس (زرین‌پال، کاوه‌نگار، توکن تلگرام و کلیدهای دیتابیس) منحصراً در فایل محیطی امن خارج از پوشه وب (`public_html`).
- [ ] PENDING : **No secrets in git:** بررسی دقیق `.gitignore` و اطمینان از اینکه هیچ رمز عبور یا توکنی در مخزن گیت متعهد (`commit`) نشود.

---

## F. Integration Order (`ترتیب یکپارچه‌سازی وب‌سرویس‌ها`)

- [ ] PENDING : **1. WooCommerce REST API keys:** تولید کلیدهای REST API ووکامرس (`Consumer Key` و `Consumer Secret`) با دسترسی `Read/Write` و ذخیره در فایل امن خارج از پوشه وب.
- [ ] PENDING : **2. Zarinpal sandbox first:** اتصال درگاه زرین‌پال ابتدا به محیط تست/سندباکس جهت بررسی عملکرد صحیح درگاه.
- [ ] PENDING : **3. Kavenegar SMS:** اتصال وب‌سرویس پیامک کاوه‌نگار (مسیر اصلی و الزامی اطلاع‌رسانی مالک و مشتری).
- [ ] PENDING : **4. Telegram optional:** اتصال ربات تلگرام مدیریت (`[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`) به عنوان کانال ثانویه اختیاری.
- [ ] PENDING : **5. Agent env on server:** استقرار اسکریپت‌های ایجنت پایتون (`agents/`) روی سرور (مشروط به موفقیت تست‌های پذیرش پایتون/کرون/شبکه) و تنظیم متغیرهای محیطی در محیط مجازی پایتون (`venv`).

---

## G. Validation Order (`ترتیب تست و اعتبارسنجی نهایی`)

- [ ] PENDING : **1. Homepage / Product page:** بررسی صحت نمایش صفحه اصلی، هدر، لوگوهای مصوب و صفحه محصول انگشتر نقره ۹۲۵ (RTL صحیح).
- [ ] PENDING : **2. Add to cart / Checkout:** تست افزودن محصول به سبد خرید و ورود به صفحه پرداخت زرین‌پال.
- [ ] PENDING : **3. SMS owner notify:** بررسی دریافت آنی پیامک هشدار ثبت سفارش جدید توسط مالک از طریق کاوه‌نگار (الزام حیاتی).
- [ ] PENDING : **4. Admin approval fallback:** تست مسیر جایگزین تأیید انسانی سفارش (`HITL Path B`)؛ تغییر دستی وضعیت از `On-Hold` به `Processing` در پنل مدیریت ووکامرس و تأیید ارسال پیامک به مشتری.
- [ ] PENDING : **5. Telegram optional path:** تست مسیر اختیاری تلگرام (`HITL Path A`) و بررسی عملکرد دکمه‌های تعاملی `[تأیید موجودی و ارسال]` و `[عدم موجودی و لغو]`.
- [ ] PENDING : **6. Backup create / download test:** اجرای دستی یک نسخه پشتیبان در UpdraftPlus، دانلود فایل دیتابیس و بررسی سلامت فایل بک‌آپ.

---

## H. Stop Line (`خط قرمز و توقف عملیات`)

> 🛑 **WARNING / STOP LINE:**  
> **DO NOT PUT RIDELIN ON THIS HOST.**  
> *این هاست منحصراً برای استقرار و ارزیابی عملیاتی برند رادمان سیلور (`RADMAN SILVER 925`) تأیید شده است. استقرار هرگونه دیتابیس، فایل یا ایجنت متعلق به برند رایدلین (`RIDELIN`) بر روی این سرور اکیداً ممنوع است.*
