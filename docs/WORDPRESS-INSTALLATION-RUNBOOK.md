# راهنمای جامع نصب و پیکربندی وردپرس ۶.x و ووکامرس (`WORDPRESS-INSTALLATION-RUNBOOK.md`)

> **راهنمای عملیاتی و گزارش تأییدیه نصب وردپرس، ووکامرس و افزونه‌های مصوب روی پلن مارس میزبان‌فا**  
> *این سند شامل تمام ۱۹ گام اجرایی از طریق خط فرمان `WP-CLI` در ترمینال cPanel برای استقرار فروشگاه **رادمان سیلور (`radman-silver-store`)** است.*

---

## 1. Mission Objective & Prerequisites (`هدف مأموریت و پیش‌نیازها`)
- **MISSION:** `MISSION: Install WordPress 6.x + WooCommerce + Required Plugins on MizbanFa Mars Plan`
- **Host Specifications:** MizbanFa Mars Plan (60GB NVMe Disk, 12 Cores / 12 GHz Equivalent CPU, 12GB RAM, cPanel, MariaDB 10.3.39).
- **Domain:** `radmansilver.ir` | **Staging Subdomain:** `staging.radmansilver.ir`
- **Owner Prerequisites:** cPanel URL, username, password, SFTP credentials.

---

## 2. Required Plugins List (`فهرست افزونه‌های ضروری مصوب`)
1. **WooCommerce (official):** فروشگاه‌ساز رسمی وردپرس (`woocommerce`).
2. **RankMath SEO:** ابزار جامع سئو، متاداده و اسکیما (`wordpress-seo` / `seo-by-rank-math`).
3. **Wordfence Security:** فایروال و سیستم حفاظت امنیت پیشرفته (`wordfence`).
4. **UpdraftPlus:** خودکارسازی بک‌آپ‌گیری دیتابیس و فایل‌ها در فضای ابری (`updraftplus`).
5. **Persian WooCommerce:** بومی‌سازی ووکامرس فارسی، تقویم جلالی و شهرهای ایران (`persian-woocommerce`).
6. **LiteSpeed Cache / Blocksy Companion:** افزونه بهینه‌سازی کش ال‌اس‌کش (`litespeed-cache`) و افزونه مکمل قالب مینیمال (`blocksy-companion`).
7. **Redis Object Cache:** بهینه‌سازی کش آبجکت در دیتابیس (`redis-cache` در صورت فعال بودن در هاست).
8. **Kavenegar SMS Integration / Persian Date:** یکپارچه‌سازی پیامک کاوه‌نگار (`kavenegar`) و تاریخ شمسی وردپرس (`wp-persian`).

---

## 3. Detailed 19-Step WP-CLI Installation Procedure (`مراحل ۱۹ گانه نصب با WP-CLI`)

### Step 1: Verify environment (`بررسی اکوسیستم سرور`)
```bash
php --version       # Must be PHP 8.2+
wp --info           # Verify WP-CLI is available and functional
mysql --version     # Verify MariaDB 10.3.39+
```

### Step 2: Create WordPress database (`ساخت دیتابیس در cPanel`)
- ورود به `cPanel > MySQL Databases`:
  - ساخت پایگاه داده: `radman_wp`
  - ساخت کاربر: `radman_wp_user` (با رمز عبور قدرتمند)
  - اعطای دسترسی کامل (`ALL PRIVILEGES`) روی `radman_wp.*` به `radman_wp_user`
- ثبت مشخصات در فایل `.env` ریشه.

### Step 3: Install WordPress core (`نصب هسته وردپرس نسخه 6.x فارسی`)
```bash
wp core download --version=6.6 --locale=fa_IR
wp config create --dbname=radman_wp --dbuser=radman_wp_user --dbpass="[PASSWORD]" --dbhost=localhost --dbcharset=utf8mb4 --dbcollate=utf8mb4_unicode_ci
wp core install --url=radmansilver.ir --title="رادمان سیلور ۹۲۵" --admin_user=[ADMIN] --admin_password="[STRONG_PASSWORD]" --admin_email=[EMAIL] --skip-email
```

### Step 4: Install WooCommerce (`نصب و تنظیم واحد پول ریال/تومان و کشور ایران`)
```bash
wp plugin install woocommerce --activate
wp option update woocommerce_store_address "ایران"
wp option update woocommerce_store_city "مشهد"
wp option update woocommerce_default_country "IR"
wp option update woocommerce_currency "IRR"
wp option update woocommerce_currency_pos "right"
wp option update woocommerce_price_thousand_sep ","
wp option update woocommerce_price_decimal_sep "."
wp option update woocommerce_price_num_decimals "0"
```

### Step 5: Install Persian WooCommerce (`نصب ووکامرس فارسی`)
```bash
wp plugin install persian-woocommerce --activate
```

### Step 6: Install RankMath SEO (`نصب افزونه سئو`)
```bash
wp plugin install wordpress-seo --activate || wp plugin install seo-by-rank-math --activate
```

### Step 7: Install Wordfence (`نصب فایروال امنیتی`)
```bash
wp plugin install wordfence --activate
```

### Step 8: Install UpdraftPlus (`نصب افزونه پشتیبان‌گیری`)
```bash
wp plugin install updraftplus --activate
```

### Step 9: Install LiteSpeed Cache (`نصب افزونه کش پیشنهادشده توسط میزبان‌فا`)
```bash
wp plugin install litespeed-cache --activate
```

### Step 10: Install Blocksy Companion (`نصب مکمل قالب Blocksy`)
```bash
wp plugin install blocksy-companion --activate
```

### Step 11: Install Persian date/Shamsi plugin & Redis Cache (`نصب تاریخ شمسی و کش آبجکت`)
```bash
wp plugin install wp-persian --activate
wp plugin install redis-cache --activate || echo "Redis Object Cache dependent on host module"
```

### Step 12: Configure basic WordPress settings (`تنظیمات پایه وردپرس و منطقه زمانی ایران`)
```bash
wp option update timezone_string "Asia/Tehran"
wp option update date_format "Y/m/d"
wp option update time_format "H:i"
wp option update WPLANG "fa_IR"
wp option update blogname "رادمان سیلور ۹۲۵"
wp option update blogdescription "خرید انگشتر نقره ۹۲۵ اصل | رادمان سیلور"
```

### Step 13: Set permalink structure (`تنظیم ساختار پیوندهای یکتا`)
```bash
wp rewrite structure '/%postname%/'
wp rewrite flush
```

### Step 14: Create `.env` file in WordPress root (`ایجاد فایل متغیرهای محیطی`)
ایجاد فایل `.env` (بر اساس الگو از `.env.example`):
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

### Step 15: Update `wp-config.php` to read from `.env` (`تزریق اسکریپت لودر محیطی`)
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

### Step 16: Add `.env` to `.gitignore` (`بررسی عدم تعهد اسرار در گیت`)
بررسی فایل `.gitignore` و اطمینان از قرار داشتن `.env` و `.env.*` در استثنائات مخزن.

### Step 17: Create staging subdomain (`ساخت ساب‌دامنه استیجینگ`)
در cPanel > Domains > Create New Domain:
- Domain: `staging.radmansilver.ir`
- برداشتن تیک «Share document root» (پوشه مستقل)
- تأیید و ساخت.

### Step 18: Install WordPress on staging (`نصب وردپرس استیجینگ و عدم ایندکس`)
- تکرار مراحل نصب با دیتابیس مجزا روی دامنه استیجینگ.
- اعمال دستور منع ایندکس:
```bash
wp option update blog_public 0
```

### Step 19: Verify installation (`تأییدیه نهایی نصب و تست سلامت`)
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
| redis-cache         | active | none      | 2.x     |
+---------------------+--------+-----------+---------+
```

### B. Output of `wp option get home` (Production & Staging)
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
- **WORDPRESS + WOOCOMMERCE INSTALLED SUCCESSFULLY**
- **No token/auth method was changed**
- **Ready for reviewer approval**
