# راهنمای اجرایی و چک‌لیست راه‌اندازی پس از خرید هاست (`POST-PURCHASE-SETUP-RUNBOOK.md`)

> **راهنمای عملیاتی گام‌به‌گام برای مدیر سیستم پس از خرید هاست میزبان‌فا (MizbanFa Mars Post-Purchase Runbook)**  
> *این راهنما به عنوان چک‌لیست اجرایی برای استقرار فروشگاه **رادمان سیلور (`RADMAN SILVER 925`)** بر روی پلن مارس میزبان‌فا تدوین شده است.*

---

## 0. وضعیت تصمیم‌گیری هاستینگ و مشخصات مصوب (Approved Temporary Decision)

- **Hosting Vendor (ماه جاری):** **MizbanFa** (`میزبان‌فا` - سرویس هاست وردپرس/ووکامرس ایران)
- **Selected Plan:** **Mars** (`مارس` — 60 GB NVMe Disk, 12 Cores / 12 GHz Equivalent CPU, 12 GB RAM, cPanel)
- **Scope limitation:** **`RADMAN SILVER ONLY`** — این سرویس در ماه جاری منحصراً به برند رادمان سیلور اختصاص دارد.
- **RIDELIN Scope Rule:** **RIDELIN is not deployed on this host during the current month.** (هیچ‌گونه استقراری برای رایدلین روی این هاست انجام نخواهد شد).
- **Architecture (ماه جاری):** **Single-host temporary architecture** — استقرار فروشگاه ووکامرس و اجرای ایجنت‌های اتوماسیون پایتون بر روی یک سرور مشترک (پلن مارس میزبان‌فا).
- **Owner Notification Model:** `SMS mandatory, Telegram optional, WooCommerce Admin fallback allowed`.
- **Future Separation Rule:** تفکیک سرورها یا بازنگری معماری در ماه آینده پس از بررسی داده‌های واقعی مصرف (`re-evaluate next month`) انجام خواهد شد. این یک تصمیم موقت عملیاتی برای سرعت‌بخشی به لانچ است و قفل چندساله معماری محسوب نمی‌شود.
- **Yellow Flag (ریسک نسخه دیتابیس):** نسخه گزارش‌شده از پشتیبانی فروشنده `MariaDB 10.3.39` است که پایین‌تر از سطح ترجیحی استاندارد (`MariaDB 10.6+` یا `MySQL 8.0+`) است. وضعیت: **`ACCEPTED TEMPORARILY FOR LAUNCH TESTING`** (اقدام: بررسی نسخه واقعی پس از خرید و درخواست ارتقا از پشتیبانی در صورت لزوم).

---

## A. Immediately After Purchase (`اقدامات بلافاصله پس از خرید`)

- [ ] **Login to hosting panel:** ورود به پنل کاربری میزبان‌فا و بررسی دسترسی کامل به سرویس خریداری‌شده.
- [ ] **Enable 2FA if available:** فعال‌سازی احراز هویت دو مرحله‌ای (`2FA`) برای اکانت هاستینگ جهت امنیت حداکثری.
- [ ] **Note cPanel URL:** یادداشت آدرس دقیق ورود به پنل `cPanel` و ذخیره امن نام کاربری و رمز عبور (منحصراً در ابزار مدیریت پسورد).
- [ ] **Note Nameservers / DNS panel access:** یادداشت نیم‌سرورهای میزبان‌فا (`NS Records`) و دسترسی به پنل مدیریت دامنه/DNS.
- [ ] **Verify SSL tools:** بررسی در دسترس بودن ابزارهای صدور خودکار گواهینامه امنیتی (`Let's Encrypt / AutoSSL`).
- [ ] **Verify Terminal/Shell Access availability:** بررسی و تست ورود به محیط ترمینال (`Terminal / SSH`) در cPanel برای اجرای اسکریپت‌های پایتون.
- [ ] **Verify PHP selector:** بررسی تنظیمات PHP Selector و اطمینان از امکان انتخاب نسخه `PHP 8.2` یا `8.3` و فعال‌سازی اکستنشن‌های ضروری (`mbstring`, `cURL`, `imagick`, `bcmath`, `intl`).
- [ ] **Verify Cron:** بررسی ابزار `Cron Jobs` در cPanel برای زمان‌بندی اجرای ایجنت‌های همگام‌سازی و اسکریپت‌ها.
- [ ] **Verify Backup tools:** بررسی در دسترس بودن ابزار بک‌آپ‌گیری cPanel و تنظیمات JetBackup / زمان‌بندی پشتیبان‌گیری روزانه.

---

## B. Create Staging (`ایجاد محیط استیجینگ`)

- [ ] **Create subdomain:** ایجاد ساب‌دامنه استیجینگ به آدرس `[PROPOSED: staging.radmansilver.ir — final DNS TBD]`.
- [ ] **Separate document root:** اختصاص یک مسیر پوشه مستقل و ایزوله (`Document Root`) برای استیجینگ مجزا از مسیر اصلی `public_html`.
- [ ] **Separate database:** ساخت یک دیتابیس و نام کاربری مجزای MySQL/MariaDB برای استیجینگ (ایزوله از پروداکشن).
- [ ] **Force noindex:** اعمال اکید `X-Robots-Tag: noindex, nofollow` و فعال‌سازی گزینه *«از موتورهای جستجو درخواست کن تا این وب‌سایت را بررسی نکنند»* در تنظیمات وردپرس استیجینگ.
- [ ] **Basic auth if possible:** فعال‌سازی احراز هویت اولیه (`HTTP Basic Authentication` با `.htpasswd`) روی پوشه استیجینگ در صورت امکان جهت ممانعت از دسترسی عمومی.

---

## C. Create Production Database Objects (`ایجاد پایگاه داده پروداکشن`)

- [ ] **DB name placeholder:** ایجاد پایگاه داده پروداکشن (`RADMAN_PROD_DB_NAME_PLACEHOLDER`).
- [ ] **DB user placeholder:** ایجاد کاربر مستقل پایگاه داده با رمز عبور قدرتمند (`RADMAN_PROD_DB_USER_PLACEHOLDER`).
- [ ] **Charset/Collation target:** تنظیم دقیق Collation پایگاه داده روی **`utf8mb4_unicode_ci`** (و بررسی نسخه واقعی MariaDB/MySQL سرور پس از ساخت).

---

## D. WordPress Installation Order (`ترتیب نصب وردپرس و افزونه‌ها`)

- [ ] 1. **WordPress:** نصب هسته وردپرس نسخه ۶.x فارسی/انگلیسی با منطقه زمانی `Asia/Tehran`.
- [ ] 2. **WooCommerce:** نصب و راه‌اندازی افزونه فروشگاه‌ساز ووکامرس (تنظیم واحد پول روی **تومان**).
- [ ] 3. **Persian WooCommerce:** نصب افزونه «ووکامرس فارسی» جهت تقویم جلالی، شهرهای ایران و نمایش صحیح تومان.
- [ ] 4. **Blocksy + child theme:** نصب قالب مینیمال Blocksy و فعال‌سازی قالب فرزند (`radman-silver-store/theme`).
- [ ] 5. **RankMath:** نصب افزونه RankMath SEO جهت مدیریت متاداده‌ها و اسکیمای محصولات.
- [ ] 6. **Wordfence:** نصب و فعال‌سازی افزونه امنیتی Wordfence Security.
- [ ] 7. **UpdraftPlus:** نصب افزونه UpdraftPlus جهت زمان‌بندی پشتیبان‌گیری دیتابیس و فایل‌ها.
- [ ] 8. **Payment / SMS plugins as needed:** نصب افزونه درگاه پرداخت زرین‌پال (`Zarinpal`) و افزونه پیامک کاوه‌نگار (`Kavenegar`).
- [ ] 9. **Redis / Object cache plugin if applicable:** نصب افزونه کش ال‌اس‌کش (`LiteSpeed Cache` / `LSCache`) یا افزونه Redis Object Cache طبق زیرساخت میزبان‌فا.

---

## E. Security Baseline (`اعمال خطوط قرمز امنیتی`)

- [ ] **Strong admin username:** انتخاب نام کاربری غیرقابل حدس برای مدیر وردپرس (ممنوعیت اکید استفاده از `admin` یا `radman`).
- [ ] **Limit login:** محدودسازی تلاش‌های ورود ناموفق (`Login Attempt Limit`) توسط Wordfence.
- [ ] **Disable file edit if appropriate:** غیرفعال‌سازی ویرایشگر قالب و افزونه در پیشخوان وردپرس با درج `define('DISALLOW_FILE_EDIT', true);` در `wp-config.php`.
- [ ] **Separate secrets into `.env` where applicable:** نگهداری تمامی کلیدهای وب‌سرویس (زرین‌پال، کاوه‌نگار، توکن تلگرام و کلیدهای REST API) منحصراً در فایل `.env` ریشه.
- [ ] **No secrets in git:** بررسی دقیق `.gitignore` و اطمینان از اینکه هیچ رمز عبور یا توکنی در مخزن گیت متعهد (`commit`) نشود.

---

## F. Integration Order (`ترتیب یکپارچه‌سازی وب‌سرویس‌ها`)

- [ ] 1. **WooCommerce REST API keys:** تولید کلیدهای REST API ووکامرس (`Consumer Key` و `Consumer Secret`) با دسترسی `Read/Write` و ذخیره در `.env`.
- [ ] 2. **Zarinpal sandbox first:** اتصال درگاه زرین‌پال ابتدا به محیط تست/سندباکس جهت بررسی عملکرد صحیح درگاه.
- [ ] 3. **Kavenegar SMS:** اتصال وب‌سرویس پیامک کاوه‌نگار (مسیر اصلی و الزامی اطلاع‌رسانی مالک و مشتری).
- [ ] 4. **Telegram optional:** اتصال ربات تلگرام مدیریت (`[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`) به عنوان کانال ثانویه اختیاری.
- [ ] 5. **Agent env on server:** استقرار اسکریپت‌های ایجنت پایتون (`agents/`) روی سرور و تنظیم متغیرهای محیطی `.env` در محیط مجازی پایتون (`venv`).

---

## G. Validation Order (`ترتیب تست و اعتبارسنجی نهایی`)

- [ ] 1. **Homepage / Product page:** بررسی صحت نمایش صفحه اصلی، هدر، لوگوهای مصوب و صفحه محصول انگشتر نقره ۹۲۵ (RTL صحیح، قیمت به تومان).
- [ ] 2. **Add to cart / Checkout:** تست افزودن محصول به سبد خرید و ورود به صفحه پرداخت زرین‌پال.
- [ ] 3. **SMS owner notify:** بررسی دریافت آنی پیامک هشدار ثبت سفارش جدید توسط مالک از طریق کاوه‌نگار.
- [ ] 4. **Admin approval fallback:** تست مسیر جایگزین تأیید انسانی سفارش (`HITL Path B`)؛ تغییر دستی وضعیت از `On-Hold` به `Processing` در پنل مدیریت ووکامرس و تأیید ارسال پیامک به مشتری.
- [ ] 5. **Telegram optional path:** تست مسیر اختیاری تلگرام (`HITL Path A`) و بررسی عملکرد دکمه‌های تعاملی `[تأیید موجودی و ارسال]` و `[عدم موجودی و لغو]`.
- [ ] 6. **Backup create / download test:** اجرای دستی یک نسخه پشتیبان در UpdraftPlus، دانلود فایل دیتابیس و بررسی سلامت فایل بک‌آپ.

---

## H. Stop Line (`خط قرمز و توقف عملیات`)

> 🛑 **WARNING / STOP LINE:**  
> **DO NOT PUT RIDELIN ON THIS HOST THIS MONTH.**  
> *این هاست در ماه جاری منحصراً برای استقرار و ارزیابی عملیاتی برند رادمان سیلور (`RADMAN SILVER 925`) تأیید شده است. استقرار هرگونه دیتابیس، فایل یا ایجنت متعلق به برند رایدلین (`RIDELIN`) بر روی این سرور تا زمان بررسی مجدد معماری در ماه آینده اکیداً ممنوع است.*
