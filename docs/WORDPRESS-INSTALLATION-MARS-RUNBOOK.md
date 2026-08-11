# راهنمای استقرار وردپرس ۶.x و ووکامرس روی پلن مارس میزبان‌فا (`WORDPRESS-INSTALLATION-MARS-RUNBOOK.md`)

> **WordPress/WooCommerce Staging Deployment Preparation Runbook — Not Yet Executed**  
> **Operational Status:** **`Preparation Runbook — Not Yet Executed`** (`DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST`)

---

## 1. Current Status (`وضعیت فعلی مأموریت`)
- **MISSION:** `MISSION: Install WordPress 6.x + WooCommerce + Required Plugins on MizbanFa Mars Plan (RADMAN only)`
- **Target Host:** MizbanFa Mars Plan (60GB NVMe Disk, 12 Cores / 12 GHz Equivalent CPU, 12GB RAM, cPanel, MariaDB 10.3.39).
- **Scope Limitation:** **`RADMAN SILVER ONLY`** (RIDELIN is strictly out of scope for this mission).
- **Official Status:** **`DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST`** — هیچ‌گونه استقرار واقعی، ایجاد دیتابیس، تنظیم DNS یا نصب افزونه روی سرور انجام نشده است. این مجموعه ابزاری برای استقرار ایمن در استیجینگ است.

---

## 2. Preflight Checks (`بررسی‌های اولیه و آمادگی محیط`)
پیش از هرگونه استقرار، دستورات فقط-خواندنی زیر برای اعتبارسنجی قابلیت‌های سرور اجرا می‌شوند:
```bash
php --version       # Exact PHP version (Must be PHP 8.2+)
wp --info           # Exact WP-CLI version
mysql --version     # Exact MySQL / MariaDB version (MariaDB 10.3.x triggers YELLOW FLAG)
python3 --version   # Exact Python 3 version
```
- **سیاست نگارش دیتابیس (`MariaDB 10.3.x`):** نسخه `MariaDB 10.3` پایین‌تر از سطح ترجیحی استاندارد (`MariaDB 10.6+` یا `MySQL 8.0+`) است؛ بنابراین اجرای اسکریپت همراه با **`YELLOW FLAG`** بوده و منحصراً برای تست سازگاری در استیجینگ با تنظیم متغیر `ALLOW_LEGACY_DB_FOR_STAGING=1` مجاز خواهد بود.
- **سیاست نگارش وردپرس و ووکامرس:** وردپرس به صورت پیش‌فرض آخرین نسخه پایدار رسمی در زمان اجرا را نصب می‌کند (نسخه پایدار در تاریخ `2026-08-10` نسخه `7.0.3` است؛ امکان اورراید با `WP_VERSION` جهت تست وجود دارد). ووکامرس آخرین نسخه پایدار زمان اجرا را نصب و نسخه دقیق گزارش می‌شود.

---

## 3. Manual cPanel Prerequisites (`پیش‌نیازهای دستی cPanel`)
اسکریپت اتوماسیون به هیچ عنوان اقدام به ایجاد منابع سی‌پنل نمی‌کند. پیش از اجرای اسکریپت، مدیر زیرساخت موظف به انجام موارد زیر در cPanel است (تمامی موارد در وضعیت `PENDING` هستند):
- [ ] **Purchase/Provision Host:** خرید و فعال‌سازی پلن مارس میزبان‌فا (`PENDING`).
- [ ] **Identify Account Home Path:** تعیین مسیر دقیق هوم دایرکتوری هاست (`PENDING`).
- [ ] **Create Independent Staging Subdomain:** ساخت ساب‌دامنه مستقل `staging.radmansilver.ir` ایزوله از پروداکشن (`PENDING`).
- [ ] **Create Prefixed Staging Database & User:** ایجاد دیتابیس و کاربر مجزای استیجینگ همراه با پیشوند سی‌پنل (مانند `prefix_radman_wp`) با دسترسی `ALL PRIVILEGES` (`PENDING`).
- [ ] **Issue and Verify SSL:** صدور و تأیید گواهینامه امنیتی `HTTPS / TLS 1.3` برای ساب‌دامنه استیجینگ (`PENDING`).
- [ ] **Identify Actual Staging Document Root:** تعیین مسیر دقیق پوشه ریشه استیجینگ مجزا از `public_html` (`PENDING`).
- [ ] **Enable Terminal/WP-CLI:** فعال‌سازی دسترسی ترمینال SSH و صحت کارکرد `WP-CLI` (`PENDING`).
- [ ] **Verify Redis Availability:** بررسی در دسترس بودن ماژول PHP Redis و سرویس Redis روی سرور (`PENDING`).

---

## 4. Secret Placement Outside Web Root (`نگهداری امن اسرار خارج از ریشه وب`)
- فایل متغیرهای محیطی `.env` هرگز نباید در `public_html`، دایرکتوری وردپرس یا مخزن گیت ذخیره شود.
- فایل اسرار باید در مسیری اختصاصی و خصوصی خارج از ریشه وب (به عنوان مثال `/home/[CPANEL_USER]/.config/radman/staging.env`) قرار گیرد.
- لودر امنیتی `config/wp-config-env.php` مسیر فایل را از متغیر محیطی `RADMAN_ENV_FILE` خوانده و با `parse_ini_file(..., INI_SCANNER_RAW)` پردازش می‌کند.

---

## 5. Staging-Only Execution (`اجرای انحصاری روی محیط استیجینگ`)
اجرای اسکریپت در محیط پروداکشن اکیداً ممنوع و مسدود است. برای اجرای استقرار روی استیجینگ، پس از تنظیم پیش‌نیازهای دستی، دستور زیر اجرا می‌شود:
```bash
export WP_PATH="/home/[CPANEL_USER]/staging.radmansilver.ir"
export WP_URL="https://staging.radmansilver.ir"
export WP_TITLE="رادمان سیلور ۹۲۵ (استیجینگ)"
export WP_LOCALE="fa_IR"
export ADMIN_USER="radman_admin"
export ADMIN_EMAIL="admin@radmansilver.ir"
export DB_NAME="[CPANEL_PREFIXED_DB_NAME]"
export DB_USER="[CPANEL_PREFIXED_DB_USER]"
export DB_HOST="localhost"
export RADMAN_ENV_FILE="/home/[CPANEL_USER]/.config/radman/staging.env"
export APP_ENV="staging"
export CONFIRM_STAGING_EXECUTION="YES"
export ALLOW_LEGACY_DB_FOR_STAGING=1  # Mandatory waiver for MariaDB 10.3 yellow flag

# Secret credentials supplied via protected server environment:
export ADMIN_PASSWORD="[PROTECTED_SERVER_SECRET]"
export DB_PASSWORD="[PROTECTED_SERVER_SECRET]"

/home/[CPANEL_USER]/radman-silver-store/scripts/install_wordpress_mars.sh --execute-staging
```

---

## 6. Theme and Plugin Compatibility Validation (`اعتبارسنجی سازگاری قالب و افزونه‌ها`)
- **WooCommerce (`woocommerce`):** فروشگاه‌ساز رسمی وردپرس.
- **RankMath SEO (`seo-by-rank-math`):** اسلاگ رسمی افزونه سئو (حذف `wordpress-seo` و عدم استفاده از Yoast).
- **Wordfence Security (`wordfence`) & UpdraftPlus (`updraftplus`):** فایروال و سیستم پشتیبان‌گیری.
- **Persian WooCommerce (`persian-woocommerce`):** بومی‌سازی ووکامرس فارسی (نصب افزونه‌های موازی تاریخ شمسی نظیر `wp-persian` یا `wp-parsidate` به منظور جلوگیری از تداخل جلالی حذف شده و در صورت نیاز در تست‌های استیجینگ جداگانه بررسی می‌شود).
- **LiteSpeed Cache (`litespeed-cache`):** افزونه رسمی کش میزبان‌فا (افزونه `WP Rocket` غیرفعال است و همزمان فعال نخواهد شد).
- **Redis Object Cache (`redis-cache`):** صرفاً در صورت موفقیت تست ارتباط `wp redis status` فعال می‌شود؛ در غیر این صورت وضعیت آن `PENDING HOST REDIS CONFIGURATION` گزارش می‌شود.
- **Blocksy Theme (`blocksy`) & Companion (`blocksy-companion`):** قالب مینیمال رادمان؛ استقرار قالب فرزند (`Blocksy Child Theme`) در وضعیت **`PENDING PACKAGE CREATION AND REVIEW`** قرار دارد.
- **Kavenegar SMS & Zarinpal:** یکپارچه‌سازی درگاه پیامک و پرداخت تا زمان شناسایی پکیج دقیق و ممیزی تنظیمات در وضعیت **`PENDING`** است.

---

## 7. Currency Safety Gate (`دروازه امنیتی واحد پول و قیمت‌گذاری`)

> ⚠️ **STAGING BLOCKER — CURRENCY SAFETY GATE:**  
> **CURRENCY STORAGE CONVENTION MUST BE VERIFIED BEFORE PRODUCT IMPORT OR PRICE AGENT ACTIVATION.**

- با توجه به اینکه ورودی‌های قیمت‌گذاری تجاری مصوب مالک به **تومان** است در حالی که اسکیمای محصولات با واحد **IRR (ریال)** تعریف می‌شود، هیچ قیمت‌گذاری یا ایمپورت محصولی در این مرحله انجام نمی‌شود.
- اگر ووکامرس روی واحد ریال (`IRR`) ذخیره‌سازی کند، قیمت‌های تومان باید پیش از نوشتن در ووکامرس با استفاده از ضریب آزمایش‌شدهٔ ۱۰ تبدیل شوند.
- خروجی‌های نمایش فروشگاه و اسکیمای JSON-LD باید به طور کامل تست شوند.
- هیچ‌گونه ورود محصول اولیه (`Product Seeding`)، همگام‌سازی قیمت یا تست پرداخت تا زمان تصویب نهایی این قاعده در مأموریت مجزا مجاز نخواهد بود.

---

## 8. Post-Install Verification (`اعتبارسنجی پس از نصب`)

هرگونه خروجی دستورات در این جدول صرفاً **مثال خروجی مورد انتظار** بوده و گواه بر اجرای واقعی روی سرور نیست:

```text
EXPECTED OUTPUT EXAMPLE — NOT ACTUAL HOST EVIDENCE
```

| Verification Check | Command to Run | Expected Condition | Actual Result | Timestamp |
| :--- | :--- | :--- | :---: | :---: |
| **Plugin List Audit** | `wp plugin list` | All approved plugins active | **`PENDING`** | **`PENDING`** |
| **Home URL Check** | `wp option get home` | `https://staging.radmansilver.ir` | **`PENDING`** | **`PENDING`** |
| **Staging Noindex Check** | `wp option get blog_public` | `0` (Strictly noindex) | **`PENDING`** | **`PENDING`** |
| **Timezone Check** | `wp option get timezone_string` | `Asia/Tehran` | **`PENDING`** | **`PENDING`** |
| **Locale Check** | `wp option get WPLANG` | `fa_IR` | **`PENDING`** | **`PENDING`** |
| **Currency Check** | `wp option get woocommerce_currency` | `IRR` | **`PENDING`** | **`PENDING`** |
| **Permalink Check** | `wp rewrite structure` | `/%postname%/` | **`PENDING`** | **`PENDING`** |
| **Database Integrity Check** | `wp db check` | `Success: Database checked. OK` | **`PENDING`** | **`PENDING`** |

---

## 9. Evidence Collection (`جمع‌آوری شواهد و گزارش‌دهی`)
هنگام اجرای واقعی در آینده، اپراتور موظف است شواهد زیر را بدون درج اطلاعات محرمانه (اسرار، نام‌های کاربری، مسیرهای دایرکتوری هوم، توکن‌ها و رمزهای عبور) جمع‌آوری کند:
- برچسب زمانی دقیق به وقت UTC و `Asia/Tehran`
- نام سرور/هاست (Sanitized Hostname)
- نسخه دقیق PHP
- نسخه دقیق پایگاه داده (`MariaDB / MySQL`)
- نسخه دقیق هسته وردپرس
- نسخه دقیق ووکامرس
- وضعیت قالب فعال و قالب فرزند (`Blocksy Child Theme Status`)
- نام دقیق و نسخه تک‌تک افزونه‌های نصب‌شده
- آدرس‌های `home` و `siteurl`
- وضعیت گزینه `blog_public`
- تأیید صحت اتصال گواهینامه HTTPS
- نتیجه سلامت پایگاه داده (`wp db check`)
- نتیجه تست سلامت `REST API` وردپرس و ووکامرس

---

## 10. Stop Conditions (`خطوط قرمز و شرایط توقف عملیات`)
در صورت بروز هر یک از ۱۲ شرط زیر، اجرای اسکریپت و عملیات استقرار باید **فوراً متوقف** شود:
1. **PHP below approved target:** نسخه PHP سرور پایین‌تر از ۸.۲ باشد.
2. **WP-CLI unavailable:** ابزار خط فرمان `WP-CLI` روی سرور نصب یا در دسترس نباشد.
3. **Actual database version not detected:** نسخه دقیق پایگاه داده قابل تشخیص و گزارش نباشد.
4. **MariaDB 10.3 without explicit staging waiver:** نسخه پایگاه داده `MariaDB 10.3` باشد و متغیر `ALLOW_LEGACY_DB_FOR_STAGING=1` ست نشده باشد.
5. **HTTPS unavailable:** گواهینامه SSL فعال نبوده یا اتصال HTTPS روی استیجینگ برقرار نباشد.
6. **Document root not empty:** مسیر پوشه ریشه استیجینگ (`WP_PATH`) خالی نبوده یا وردپرس از قبل در آن نصب باشد.
7. **Staging database not independent:** پایگاه داده استیجینگ با پروداکشن مشترک باشد.
8. **Secret file inside web root:** فایل اسرار `.env` داخل ریشه وب (`public_html` یا دایرکتوری استیجینگ) قرار داشته باشد.
9. **Plugin/theme slug unavailable:** هر یک از اسلاگ‌های رسمی افزونه‌ها یا قالب در مخزن وردپرس ناموجود یا ناسازگار باشد.
10. **Redis expected but connectivity failed:** ارتباط با سرویس Redis برقرار نباشد در حالی که فعال‌سازی اجباری کش آبجکت درخواست شده باشد.
11. **WordPress/WooCommerce/plugin compatibility unresolved:** تداخل سازگاری میان نگارش وردپرس، ووکامرس یا افزونه‌ها مشاهده شود.
12. **Staging URL resolving to production directory:** آدرس استیجینگ به مسیر پروداکشن (`public_html`) اشاره کند.

---

## 11. Production Deployment Deferred (`به تعویق افتادن استقرار پروداکشن`)
استقرار وردپرس و ووکامرس روی دامنه اصلی پروداکشن (`radmansilver.ir`) در این ابزار و راهنما **اکیداً ممنوع** است. ورود به مرحله پروداکشن نیازمند تأیید نهایی عملکرد استیجینگ، ممیزی امنیتی و صدور مأموریت مستقل مصوب توسط بازبین پروژه خواهد بود.

---

## 12. Official Mission Status Statement (`اعلامیه رسمی وضعیت مأموریت`)
- **DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST**
- **PR #9 CLOSED WITHOUT MERGE AS DUPLICATE**
- **PR #10 UPDATED, NOT MERGED**
- **PR #8 WAS NOT TOUCHED**
- **No token/auth method was changed**
- **Ready for reviewer approval**
