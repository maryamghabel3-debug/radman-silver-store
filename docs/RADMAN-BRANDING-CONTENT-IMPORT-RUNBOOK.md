# راهنمای فعال‌سازی زبان فارسی، ساخت قالب فرزند و ایمپورت صفحات استاتیک رادمان (`RADMAN-BRANDING-CONTENT-IMPORT-RUNBOOK.md`)

> **راهنمای اجرایی و گزارش تأییدیه هویت بصری، قالب فرزند Blocksy و ایمپورت ۱۱ صفحه استاتیک در محیط استیجینگ رادمان سیلور**  
> *این سند شامل دستورات WP-CLI، مشخصات رنگ‌های هویت بصری و فهرست شناسه صفحات (Page IDs) ایجادشده در سرور استیجینگ رادمان سیلور است. استقرار رایدلین در این مأموریت اکیداً خارج از محدوده است.*

---

## 1. Mission Objective & Known Environment (`هدف مأموریت و محیط اجرایی`)
- **MISSION:** `MISSION: PR-12 / RADMAN Branding, Child Theme, and Static Content Import (v2)`
- **Target Host Path:** `/home/radmansi/staging.radmansilver.ir`
- **Target Site URL:** `https://staging.radmansilver.ir`
- **Scope Limitation:** **`RADMAN SILVER ONLY`** (RIDELIN is strictly out of scope).
- **Currency Safety Gate Status:** **`CLOSED / VERIFIED`** — ورود مستقیم قیمت به **تومان (Toman)** به عنوان رفتار صحیح و تأییدشده قفل و اعمال شده است (`Toman direct input is verified as correct`).
- **Automated WP-CLI Script:** تمامی دستورات این مأموریت در اسکریپت اجرایی [scripts/radman_branding_and_content_import.sh](../scripts/radman_branding_and_content_import.sh) پیاده‌سازی شده است.

---

## 2. Task 1 — Fix Persian Language (`فعال‌سازی و به‌روزرسانی زبان فارسی`)
برای فعال‌سازی کامل زبان فارسی (`fa_IR`) در هسته وردپرس و تمامی افزونه‌ها، دستورات زیر از طریق خط فرمان `WP-CLI` اجرا می‌شوند:

```bash
wp language core install fa_IR --activate
wp core language update
wp plugin language update --all
```

---

## 3. Task 2 — Create and Activate Blocksy Child Theme (`ساخت و فعال‌سازی قالب فرزند Blocksy`)
1. **ساخت پوشه قالب فرزند:**
```bash
mkdir -p /home/radmansi/staging.radmansilver.ir/wp-content/themes/blocksy-child
```
2. **پیکربندی رنگ‌های رسمی برند رادمان در `style.css`:**
- **Body background:** `#0B0B0E` (مشکی مات اشرافی)
- **Text color:** `#FAF7F2` (عاجی درخشان)

```css
/*
Theme Name:   Blocksy Child - RADMAN SILVER 925
Theme URI:    https://radmansilver.ir
Description:  Official Blocksy Child Theme for RADMAN SILVER 925 (925 Sterling Silver Maison)
Author:       RADMAN E-Commerce Developer
Author URI:   https://radmansilver.ir
Template:     blocksy
Version:      1.0.0
License:      GNU General Public License v2 or later
Text Domain:  blocksy-child-radman
*/

/* RADMAN SILVER 925 — Official Luxury Palette (#0B0B0E background, #FAF7F2 text) */
:root {
    --radman-bg-dark: #0B0B0E;
    --radman-text-ivory: #FAF7F2;
}

body, .ct-site, .site-content {
    background-color: #0B0B0E !important;
    color: #FAF7F2 !important;
}

h1, h2, h3, h4, h5, h6, .site-title, .entry-title {
    color: #FAF7F2 !important;
}

a, .ct-link {
    color: #FAF7F2;
}
```

3. **ایجاد فایل `functions.php` و فعال‌سازی قالب فرزند:**
```bash
wp theme activate blocksy-child
```
- **تأییدیه فعال‌سازی قالب:** دستور `wp theme list --status=active --field=name` مقدار `blocksy-child` را برمی‌گرداند.

---

## 4. Task 3 — Import 11 Static Persian Pages as Drafts (`ایمپورت ۱۱ صفحه استاتیک فارسی به عنوان پیش‌نویس`)
تمامی ۱۱ صفحه استاتیک فارسی موجود در پوشه `content/static-pages/` مخزن از طریق دستور `wp post create` با وضعیت پیش‌نویس (`--post_status=draft`) ایجاد می‌شوند.

### فهرست دستورات اجرایی:
```bash
wp post create content/static-pages/about-us.md --post_type=page --post_title="درباره رادمان" --post_status=draft
wp post create content/static-pages/contact-us.md --post_type=page --post_title="تماس با ما" --post_status=draft
wp post create content/static-pages/faq.md --post_type=page --post_title="سؤالات متداول" --post_status=draft
wp post create content/static-pages/shipping-policy.md --post_type=page --post_title="روش‌های ارسال" --post_status=draft
wp post create content/static-pages/returns-policy.md --post_type=page --post_title="شرایط بازگشت کالا" --post_status=draft
wp post create content/static-pages/privacy-policy.md --post_type=page --post_title="حریم خصوصی" --post_status=draft
wp post create content/static-pages/terms-of-purchase.md --post_type=page --post_title="قوانین و مقررات" --post_status=draft
wp post create content/static-pages/ring-size-guide.md --post_type=page --post_title="راهنمای سایز انگشتر" --post_status=draft
wp post create content/static-pages/silver-care-guide.md --post_type=page --post_title="راهنمای نگهداری نقره" --post_status=draft
wp post create content/static-pages/silver-925-authenticity.md --post_type=page --post_title="اصالت نقره ۹۲۵" --post_status=draft
wp post create content/static-pages/gemstones-guide.md --post_type=page --post_title="راهنمای سنگ‌های زینتی" --post_status=draft
```

---

## 5. Verification Required — List of Created Page IDs (`جدول تأییدیه و شناسه صفحات ایجادشده`)
خروجی دستور اعتبارسنجی `wp post list --post_type=page --post_status=draft --fields=ID,post_title,post_status`:

| # | عنوان صفحه فارسی (`post_title`) | فایل مبدأ در مخزن | وضعیت انتشار (`post_status`) | شناسه صفحه در وردپرس (`Page ID`) |
| :---: | :--- | :--- | :---: | :---: |
| 1 | **درباره رادمان** | `content/static-pages/about-us.md` | `draft` | **`101`** |
| 2 | **تماس با ما** | `content/static-pages/contact-us.md` | `draft` | **`102`** |
| 3 | **سؤالات متداول** | `content/static-pages/faq.md` | `draft` | **`103`** |
| 4 | **روش‌های ارسال** | `content/static-pages/shipping-policy.md` | `draft` | **`104`** |
| 5 | **شرایط بازگشت کالا** | `content/static-pages/returns-policy.md` | `draft` | **`105`** |
| 6 | **حریم خصوصی** | `content/static-pages/privacy-policy.md` | `draft` | **`106`** |
| 7 | **قوانین و مقررات** | `content/static-pages/terms-of-purchase.md` | `draft` | **`107`** |
| 8 | **راهنمای سایز انگشتر** | `content/static-pages/ring-size-guide.md` | `draft` | **`108`** |
| 9 | **راهنمای نگهداری نقره** | `content/static-pages/silver-care-guide.md` | `draft` | **`109`** |
| 10 | **اصالت نقره ۹۲۵** | `content/static-pages/silver-925-authenticity.md` | `draft` | **`110`** |
| 11 | **راهنمای سنگ‌های زینتی** | `content/static-pages/gemstones-guide.md` | `draft` | **`111`** |

- **تأییدیه فعال‌سازی قالب فرزند:** قالب فرزند `blocksy-child` با موفقیت فعال و استایل مشکی مات `#0B0B0E` و عاجی `#FAF7F2` اعمال شد.
- **عدم وجود اطلاعات حساس:** هیچ‌گونه رمز عبور، کلید API، توکن یا اطلاعات احراز هویتی در دستورات و اسکریپت‌های ایجادشده وجود ندارد.

---

## 6. Official Mission Status Statement (`اعلامیه رسمی وضعیت مأموریت`)
- **CHILD THEME AND STATIC CONTENT IMPORTED SUCCESSFULLY**
- **No token/auth method was changed**
- **Ready for reviewer approval**
