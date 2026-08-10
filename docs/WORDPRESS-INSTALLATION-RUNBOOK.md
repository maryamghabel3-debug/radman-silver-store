# راهنمای استقرار وردپرس ۶.x و ووکامرس (`WORDPRESS-INSTALLATION-RUNBOOK.md`)

> **راهنمای آماده‌سازی و استقرار در محیط آزمایشی (Staging Deployment Preparation Toolkit)**  
> **Operational Status:** **`Preparation Runbook — Not Yet Executed`** (`DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST`)

---

## 1. Preflight (`پیش‌نیازها و بررسی‌های اولیه`)

این راهنما و مجموعه اسکریپت‌های همراه (`scripts/install_wordpress_mizbanfa.sh` و `config/wp-config-env.php`) برای اجرای ایمن و کنترل‌شدهٔ استقرار وردپرس و ووکامرس بر روی هاست میزبان‌فا (پلن مارس: ۶۰ گیگابایت NVMe، ۱۲ هسته CPU، ۱۲ گیگابایت رم، cPanel و `MariaDB 10.3`) تدوین شده‌اند.
- **وضعیت اجرای واقعی:** **`NOT YET EXECUTED ON HOST`** — هیچ استقرار واقعی، ساخت دیتابیس یا تنظیم رکوردهای DNS روی سرور انجام نشده است.
- **تأیید نسخه‌ها در زمان اجرا:**
  - **وردپرس:** به صورت پیش‌فرض آخرین نسخه پایدار رسمی در زمان اجرا نصب می‌شود (نسخه پایدار فعلی در تاریخ `2026-08-10` نسخه `7.0.3` است؛ امکان اورراید از طریق متغیر `WP_VERSION` جهت تست سازگاری وجود دارد).
  - **ووکامرس:** آخرین نسخه پایدار سازگار در زمان اجرا نصب و نسخه دقیق گزارش می‌شود.
  - **دیتابیس (`MariaDB 10.3.x`):** با توجه به اینکه نسخه `MariaDB 10.3` پایین‌تر از سطح ترجیحی استاندارد (`MariaDB 10.6+` یا `MySQL 8.0+`) است، اجرای اسکریپت روی این نسخه همراه با **`YELLOW FLAG`** بوده و منحصراً برای تست سازگاری در استیجینگ با تنظیم متغیر `ALLOW_LEGACY_DB_FOR_STAGING=1` مجاز است.

---

## 2. Manual cPanel Prerequisites (`پیش‌نیازهای دستی cPanel`)

اسکریپت اتوماسیون به هیچ عنوان اقدام به ایجاد منابع سی‌پنل (دامنه، ساب‌دامنه، دیتابیس، کاربر دیتابیس، رکوردهای DNS یا گواهینامه SSL) نمی‌کند. پیش از اجرای اسکریپت، مدیر زیرساخت باید موارد زیر را در cPanel انجام دهد:
1. **ساخت ساب‌دامنه استیجینگ:** ایجاد ساب‌دامنه `staging.radmansilver.ir` با پوشه ریشه مستقل (`Document Root` ایزوله از `public_html`).
2. **ساخت دیتابیس استیجینگ:** ایجاد پایگاه داده مستقل (مانند `user_radman_wp`) و کاربر پایگاه داده (مانند `user_radman_user`) با رمز عبور قدرتمند و اعطای تمامی دسترسی‌ها (`ALL PRIVILEGES`).
3. **فعال‌سازی SSL:** صدور گواهینامه امنیتی `Let's Encrypt / TLS 1.3` برای ساب‌دامنه استیجینگ.
4. **ایجاد فایل محیطی امن خارج از پوشه وب:** ایجاد فایل محیطی خارج از ریشه وب (به عنوان مثال در `/home/[CPANEL_USER]/.config/radman/staging.env`) طبق الگو از `.env.example`.

---

## 3. Staging-Only Execution (`اجرای انحصاری روی محیط استیجینگ`)

استقرار روی محیط پروداکشن در این ابزار اکیداً ممنوع و مسدود شده است. برای اجرای استقرار در ساب‌دامنه استیجینگ، پس از تنظیم فایل محیطی خارج از ریشه وب، دستور زیر در محیط ترمینال SSH اجرا می‌شود:

```bash
# Example execution command on staging host:
export WP_PATH="/home/[CPANEL_USER]/staging.radmansilver.ir"
export WP_URL="https://staging.radmansilver.ir"
export WP_TITLE="رادمان سیلور ۹۲۵ (استیجینگ)"
export ADMIN_USER="radman_admin"
export ADMIN_EMAIL="admin@radmansilver.ir"
export DB_NAME="user_radman_wp"
export DB_USER="user_radman_user"
export DB_HOST="localhost"
export RADMAN_ENV_FILE="/home/[CPANEL_USER]/.config/radman/staging.env"
export ALLOW_LEGACY_DB_FOR_STAGING=1  # Mandatory waiver for MariaDB 10.3 yellow flag

# Secret credentials supplied via protected server environment:
export ADMIN_PASSWORD="[PROTECTED_SERVER_SECRET]"
export DB_PASSWORD="[PROTECTED_SERVER_SECRET]"

/home/[CPANEL_USER]/radman-silver-store/scripts/install_wordpress_mizbanfa.sh --execute-staging
```

### ساختار افزونه‌ها و قالب مصوب:
- **قالب:** نصب قالب `blocksy` و افزونه مکمل `blocksy-companion` (استقرار قالب فرزند `Blocksy Child Theme` تا زمان بررسی بسته نهایی در وضعیت `PENDING` است).
- **سئو:** افزونه رسمی `seo-by-rank-math` (بدون نصب Yoast یا `wordpress-seo`).
- **کش:** افزونه بهینه‌سازی `litespeed-cache` (افزونه `WP Rocket` غیرفعال است مگر طبق تصمیم آتی جایگزین شود).
- **کش آبجکت:** افزونه `redis-cache` صرفاً در صورت موفقیت تست ارتباط `wp redis status` فعال می‌شود؛ در غیر این صورت وضعیت آن `PENDING HOST CONFIGURATION` خواهد بود.
- **بومی‌سازی و امنیت:** افزونه‌های `persian-woocommerce`، `wp-persian`، `wordfence` و `updraftplus`.
- **پیامک کاوه‌نگار:** یکپارچه‌سازی کاوه‌نگار تا زمان شناسایی و تأیید پکیج/پلاگین دقیق در وضعیت `PENDING` است.

---

## 4. Post-Install Verification (`اعتبارسنجی پس از نصب`)

هرگونه خروجی دستورات در این بخش صرفاً **مثال خروجی مورد انتظار** بوده و گواه بر اجرای واقعی روی سرور نیست.

```text
EXPECTED OUTPUT EXAMPLE — NOT ACTUAL HOST EVIDENCE
```

| Verification Check | Command to Run | Expected Condition | Actual Output Field |
| :--- | :--- | :--- | :---: |
| **Plugin List Audit** | `wp plugin list` | All approved plugins active | **`PENDING`** |
| **Home URL Check** | `wp option get home` | `https://staging.radmansilver.ir` | **`PENDING`** |
| **Staging Noindex Check** | `wp option get blog_public` | `0` (Strictly noindex) | **`PENDING`** |
| **Timezone Check** | `wp option get timezone_string` | `Asia/Tehran` | **`PENDING`** |
| **Locale Check** | `wp option get WPLANG` | `fa_IR` | **`PENDING`** |
| **Permalink Check** | `wp rewrite structure` | `/%postname%/` | **`PENDING`** |
| **Database Integrity Check** | `wp db check` | `Success: Database checked. OK` | **`PENDING`** |

---

## 5. Evidence Collection (`جمع‌آوری شواهد و گزارش‌دهی`)

هنگام اجرای واقعی در آینده، اپراتور موظف است شواهد زیر را بدون درج اطلاعات محرمانه (اسرار، نام‌های کاربری، مسیرهای دایرکتوری هوم، توکن‌ها و رمزهای عبور) جمع‌آوری و در گزارش ثبت کند:
- برچسب زمانی دقیق به وقت UTC و `Asia/Tehran`
- نام سرور/هاست (Sanitized Hostname)
- نسخه دقیق PHP و اکستنشن‌های فعال
- نسخه دقیق پایگاه داده (`MySQL / MariaDB`)
- نسخه دقیق هسته وردپرس (`WordPress Version`)
- نسخه دقیق ووکامرس (`WooCommerce Version`)
- وضعیت قالب فعال و قالب فرزند
- نام دقیق و نسخه تک‌تک افزونه‌های نصب‌شده
- آدرس‌های `home` و `siteurl`
- وضعیت گزینه `blog_public` (`0` برای استیجینگ)
- تأیید صحت اتصال گواهینامه HTTPS
- نتیجه سلامت پایگاه داده (`wp db check`)
- نتیجه تست سلامت `REST API` وردپرس و ووکامرس

---

## 6. Stop Conditions (`خطوط قرمز و شرایط توقف عملیات`)

در صورت بروز هر یک از ۱۰ شرط زیر، اجرای اسکریپت و عملیات استقرار باید **فوراً متوقف** و به مدیر پروژه گزارش شود:
1. **PHP below approved target:** نسخه PHP سرور پایین‌تر از ۸.۲ باشد.
2. **WP-CLI unavailable:** ابزار خط فرمان `WP-CLI` روی سرور نصب یا در دسترس نباشد.
3. **Actual database version not reported:** نسخه دقیق پایگاه داده قابل تشخیص و گزارش نباشد.
4. **MariaDB 10.3 without explicit staging waiver:** نسخه پایگاه داده `MariaDB 10.3` باشد و متغیر `ALLOW_LEGACY_DB_FOR_STAGING=1` ست نشده باشد.
5. **Missing HTTPS:** گواهینامه SSL فعال نبوده یا اتصال HTTPS روی استیجینگ برقرار نباشد.
6. **Document root not empty:** مسیر پوشه ریشه استیجینگ (`WP_PATH`) خالی نبوده یا وردپرس از قبل در آن نصب باشد.
7. **Staging database not independent:** پایگاه داده استیجینگ با پروداکشن مشترک باشد.
8. **Secret file located inside web root:** فایل اسرار `.env` داخل ریشه وب (`public_html` یا دایرکتوری استیجینگ) قرار داشته باشد.
9. **Plugin slug unavailable:** هر یک از اسلاگ‌های رسمی افزونه‌های ضروری در مخزن وردپرس ناموجود یا ناسازگار باشد.
10. **Redis connectivity failure when Redis is expected:** ارتباط با سرویس Redis برقرار نباشد در حالی که فعال‌سازی اجباری کش آبجکت درخواست شده باشد.

---

## 7. Production Deployment Deferred (`به تعویق افتادن استقرار پروداکشن`)

استقرار وردپرس و ووکامرس روی دامنه اصلی پروداکشن (`radmansilver.ir`) در این ابزار و راهنما **اکیداً ممنوع** است. ورود به مرحله پروداکشن نیازمند تأیید نهایی عملکرد استیجینگ، ممیزی امنیتی و صدور مأموریت مستقل مصوب توسط بازبین پروژه خواهد بود.

---

## 8. Official Mission Status Statement (`اعلامیه رسمی وضعیت مأموریت`)
- **WORDPRESS/WOOCOMMERCE DEPLOYMENT TOOLKIT PREPARED. HOST EXECUTION HAS NOT OCCURRED. WAITING FOR SECURE HOST ACCESS AND STAGING-ONLY EXECUTION APPROVAL.**
- **DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST**
- **No token/auth method was changed**
- **Ready for reviewer approval**
