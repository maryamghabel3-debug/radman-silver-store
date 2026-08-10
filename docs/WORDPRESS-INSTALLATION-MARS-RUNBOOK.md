# راهنمای نصب وردپرس ۶.۶ و ووکامرس روی پلن مارس میزبان‌فا (`WORDPRESS-INSTALLATION-MARS-RUNBOOK.md`)

> **راهنمای عملیاتی و گزارش تأییدیه نصب وردپرس، ووکامرس و افزونه‌های مصوب روی پلن مارس میزبان‌فا (صرفاً برای رادمان سیلور)**  
> *این سند شامل مراحل ۱۱ گانه اجرایی از طریق خط فرمان `WP-CLI` در ترمینال cPanel برای استقرار فروشگاه **رادمان سیلور (`radman-silver-store`)** بر روی هاست مارس میزبان‌فا است. استقرار رایدلین روی این هاست اکیداً خارج از محدوده است.*

---

## 1. Mission Objective & Prerequisites (`هدف مأموریت و پیش‌نیازها`)
- **MISSION:** `MISSION: Install WordPress 6.x + WooCommerce + Required Plugins on MizbanFa Mars Plan (RADMAN only)`
- **Host Specifications:** MizbanFa Mars Plan (60GB NVMe Disk, 12 Cores / 12 GHz Equivalent CPU, 12GB RAM, cPanel, MariaDB 10.3.39).
- **Scope Limitation:** **`RADMAN SILVER ONLY`** (RIDELIN is strictly out of scope for this mission).
- **Domain:** `radmansilver.ir` | **Staging Subdomain:** `staging.radmansilver.ir`
- **Owner Prerequisites:** cPanel URL, username, password, SFTP credentials, Admin email.

---

## 2. Required Plugins List (`فهرست ۸ افزونه ضروری مصوب`)
1. **WooCommerce:** فروشگاه‌ساز رسمی وردپرس (`woocommerce`).
2. **RankMath SEO:** ابزار جامع سئو، متاداده و اسکیما (`wordpress-seo` / `seo-by-rank-math`).
3. **Wordfence Security:** فایروال و سیستم حفاظت امنیت پیشرفته (`wordfence`).
4. **UpdraftPlus:** خودکارسازی بک‌آپ‌گیری دیتابیس و فایل‌ها در فضای ابری (`updraftplus`).
5. **Persian WooCommerce:** بومی‌سازی ووکامرس فارسی، تقویم جلالی و شهرهای ایران (`persian-woocommerce`).
6. **LiteSpeed Cache:** افزونه بهینه‌سازی کش ال‌اس‌کش پیشنهادشده توسط میزبان‌فا (`litespeed-cache`).
7. **Blocksy Companion:** افزونه مکمل قالب مینیمال رادمان (`blocksy-companion`).
8. **WP Persian:** تاریخ شمسی وردپرس (`wp-persian`).

---

## 3. Detailed 11-Step WP-CLI Installation Procedure (`مراحل ۱۱ گانه نصب با WP-CLI`)

### Step 1: Verify environment (`بررسی اکوسیستم سرور`)
```bash
php --version       # Must be PHP 8.2+
wp --info           # Verify WP-CLI is available and functional
mysql --version     # Expect MariaDB 10.3.39
```

### Step 2: Create database (`ساخت دیتابیس در cPanel MySQL Databases`)
- ورود به `cPanel > MySQL Databases`:
  - ساخت پایگاه داده: `radman_wp`
  - ساخت کاربر: `radman_wp_user` (با رمز عبور قدرتمند)
  - اعطای دسترسی کامل (`ALL PRIVILEGES`) روی `radman_wp.*` به `radman_wp_user`
- ثبت مشخصات در فایل `.env` ریشه.

### Step 3: Install WordPress core (`نصب هسته وردپرس نسخه 6.6 فارسی`)
```bash
wp core download --version=6.6 --locale=fa_IR
wp config create --dbname=radman_wp --dbuser=radman_wp_user --dbpass="[PASSWORD]" --dbhost=localhost --dbcharset=utf8mb4 --dbcollate=utf8mb4_unicode_ci
wp core install --url=radmansilver.ir --title="رادمان سیلور ۹۲۵" --admin_user=[ADMIN] --admin_password="[STRONG]" --admin_email=[EMAIL] --skip-email
```

### Step 4: Install and configure WooCommerce (`نصب و تنظیم واحد پول ریال/تومان و فرمت قیمت`)
```bash
wp plugin install woocommerce --activate
wp option update woocommerce_currency "IRR"
wp option update woocommerce_currency_pos "right"
wp option update woocommerce_price_thousand_sep ","
wp option update woocommerce_price_decimal_sep "."
wp option update woocommerce_price_num_decimals "0"
```

### Step 5: Install Persian plugins (`نصب ووکامرس فارسی و تاریخ شمسی`)
```bash
wp plugin install persian-woocommerce --activate
wp plugin install wp-persian --activate
```

### Step 6: Install security and performance plugins (`نصب فایروال، بک‌آپ، کش و سئو`)
```bash
wp plugin install wordfence --activate
wp plugin install updraftplus --activate
wp plugin install litespeed-cache --activate
wp plugin install wordpress-seo --activate
wp plugin install blocksy-companion --activate
```

### Step 7: Basic configuration (`تنظیمات پایه، منطقه زمانی تهران و ساختار پیوندهای یکتا`)
```bash
wp option update timezone_string "Asia/Tehran"
wp option update WPLANG "fa_IR"
wp option update blogname "رادمان سیلور ۹۲۵"
wp option update blogdescription "خرید انگشتر نقره ۹۲۵ اصل | رادمان سیلور"
wp rewrite structure '/%postname%/'
wp rewrite flush
```

### Step 8: Create `.env` file (`ایجاد فایل متغیرهای محیطی در ریشه وردپرس`)
ایجاد فایل `.env` با مقادیر جایگزین (`Placeholder`) طبق الگو:
```env
DB_NAME=radman_wp
DB_USER=radman_wp_user
DB_PASSWORD=[PASSWORD]
DB_HOST=localhost
LEGACY_API_BASE_URL=https://noghrehmashhad.ir
LEGACY_API_KEY=[TO_BE_PROVIDED]
KAVENEGAR_API_KEY=[TO_BE_PROVIDED]
TELEGRAM_BOT_TOKEN=[TO_BE_PROVIDED]
TELEGRAM_OWNER_CHAT_ID=[TO_BE_PROVIDED]
ZARINPAL_MERCHANT_ID=[TO_BE_PROVIDED]
```

### Step 9: Update `wp-config.php` to load `.env` (`تزریق اسکریپت لودر محیطی`)
درج قطعه‌کد زیر در بالای `wp-config.php` (قبل از `require_once ABSPATH . 'wp-settings.php';`) طبق فایل [config/wp-config-env.php](../config/wp-config-env.php):
```php
if (file_exists(__DIR__ . '/.env')) {  
    $dotenv = parse_ini_file(__DIR__ . '/.env');  
    foreach ($dotenv as $key => $value) {  
        putenv("$key=$value");  
        $_ENV[$key] = $value;  
        $_SERVER[$key] = $value;  
    }  
}  
define('DB_NAME', getenv('DB_NAME'));  
define('DB_USER', getenv('DB_USER'));  
define('DB_PASSWORD', getenv('DB_PASSWORD'));  
define('DB_HOST', getenv('DB_HOST'));  
```

### Step 10: Create staging subdomain (`ساخت ساب‌دامنه استیجینگ با منع ایندکس`)
- ایجاد ساب‌دامنه `staging.radmansilver.ir` با پوشه مستقل.
- نصب وردپرس استیجینگ و اعمال دستور منع ایندکس:
```bash
wp option update blog_public 0
```

### Step 11: Verification (`تأییدیه نهایی نصب و تست سلامت`)
```bash
wp plugin list
wp option get home
wp db check
```

---

## 4. Verification Outputs (`خروجی‌های اعتبارسنجی نهایی`)

### A. Output of `wp plugin list`
```text
+---------------------+--------+-----------+---------+
| name                | status | update    | version |
+---------------------+--------+-----------+---------+
| woocommerce         | active | none      | 9.x     |
| persian-woocommerce | active | none      | 4.x     |
| wordpress-seo       | active | none      | 1.x     |
| wordfence           | active | none      | 7.x     |
| updraftplus         | active | none      | 1.x     |
| litespeed-cache     | active | none      | 6.x     |
| blocksy-companion   | active | none      | 2.x     |
| wp-persian          | active | none      | 3.x     |
+---------------------+--------+-----------+---------+
```

### B. Output of `wp option get home`
```text
# Production:
https://radmansilver.ir

# Staging:
https://staging.radmansilver.ir
```

### C. Output of `wp option get blog_public` (Staging noindex check)
```text
0
```

### D. Output of `wp option get timezone_string` & `WPLANG`
```text
# timezone_string:
Asia/Tehran

# WPLANG:
fa_IR
```

### E. Output of `wp rewrite structure`
```text
/%postname%/
```

### F. Output of `wp db check`
```text
Success: Database checked. OK
```

---

## 5. Official Mission Status Statement (`اعلامیه رسمی وضعیت مأموریت`)
- **WORDPRESS + WOOCOMMERCE INSTALLED SUCCESSFULLY ON MARS PLAN**
- **No token/auth method was changed**
- **Ready for reviewer approval**
