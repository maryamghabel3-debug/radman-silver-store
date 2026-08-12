# راهنمای فعال‌سازی زبان فارسی، ساخت قالب فرزند و ایمپورت صفحات استاتیک رادمان (`RADMAN-BRANDING-CONTENT-IMPORT-RUNBOOK.md`)

> **راهنمای اجرایی و گزارش تأییدیه هویت بصری، قالب فرزند Blocksy و ایمپورت ۱۱ صفحه استاتیک در محیط استیجینگ رادمان سیلور**  
> *این سند شامل دستورات WP-CLI، مشخصات رنگ‌های هویت بصری و فهرست واقعی و تأییدشدهٔ شناسه صفحات (Page IDs) ایجادشده در سرور استیجینگ رادمان سیلور است. استقرار رایدلین در این مأموریت اکیداً خارج از محدوده است.*

---

## 1. Mission Objective & Verified Environment (`هدف مأموریت و محیط تأییدشده`)
- **MISSION:** `MISSION: PR-12 / Record RADMAN Child Theme, Language Fix, and Static Pages (sanitized evidence)`
- **Target Host Path:** `/home/radmansi/staging.radmansilver.ir`
- **Target Site URL:** `https://staging.radmansilver.ir`
- **Scope Limitation:** **`RADMAN SILVER ONLY`** (RIDELIN is strictly out of scope).
- **Currency Safety Gate Status:** **`CLOSED / VERIFIED`** — واحد پول ووکامرس به درستی به صورت **IRT (تومان ایران / Iranian Toman)** نمایش داده می‌شود و ورود مستقیم قیمت به تومان به عنوان رفتار صحیح و تأییدشده قفل و اعمال شده است (`WooCommerce currency displays as IRT - confirmed correct per Currency Safety Gate testing`).
- **Search Engine Indexing (`noindex`):** `blog_public = 0` (`noindex confirmed, still active`).
- **Static Front Page:** صفحه اصلی (`Home page`) با شناسه **`18`** منتشر و به عنوان صفحه اصلی استاتیک سایت تنظیم شد.
- **Duplicate / Sample Pages Cleanup:** صفحات اضافی و تکراری (sample page، duplicate refund policy و duplicate privacy policy) به طور کامل حذف و پاکسازی شدند.
- **Automated WP-CLI Script:** تمامی دستورات این مأموریت در اسکریپت اجرایی [scripts/radman_branding_and_content_import.sh](../scripts/radman_branding_and_content_import.sh) پیاده‌سازی شده است.

---

## 2. Task 1 — Fix Persian Language (`فعال‌سازی و به‌روزرسانی زبان فارسی`)
زبان فارسی (`fa_IR`) در هسته وردپرس و تمامی افزونه‌ها فعال و تأیید شد (`wp option get WPLANG = fa_IR`):

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
- **تأییدیه فعال‌سازی قالب:** قالب فرزند **`blocksy-child v1.0.0`** فعال و تأیید شد (`confirmed via wp theme list`).

---

## 4. Task 3 — Import 11 Static Persian Pages as Drafts (`ایمپورت ۱۱ صفحه استاتیک فارسی به عنوان پیش‌نویس`)
تمامی ۱۱ صفحه استاتیک فارسی موجود در پوشه `content/static-pages/` مخزن از طریق دستور `wp post create` با وضعیت پیش‌نویس (`--post_status=draft`) ایجاد شدند.

### فهرست دستورات اجرایی:
```bash
wp post create content/static-pages/about-us.md --post_type=page --post_title="درباره رادمان" --post_name="about-us" --post_status=draft
wp post create content/static-pages/contact-us.md --post_type=page --post_title="تماس با ما" --post_name="contact-us" --post_status=draft
wp post create content/static-pages/faq.md --post_type=page --post_title="سؤالات متداول" --post_name="faq" --post_status=draft
wp post create content/static-pages/shipping-policy.md --post_type=page --post_title="روش‌های ارسال" --post_name="shipping" --post_status=draft
wp post create content/static-pages/returns-policy.md --post_type=page --post_title="شرایط بازگشت کالا" --post_name="returns" --post_status=draft
wp post create content/static-pages/privacy-policy.md --post_type=page --post_title="حریم خصوصی" --post_name="privacy-policy-radman" --post_status=draft
wp post create content/static-pages/terms-of-purchase.md --post_type=page --post_title="قوانین و مقررات" --post_name="terms" --post_status=draft
wp post create content/static-pages/ring-size-guide.md --post_type=page --post_title="راهنمای سایز انگشتر" --post_name="ring-size-guide" --post_status=draft
wp post create content/static-pages/silver-care-guide.md --post_type=page --post_title="راهنمای نگهداری نقره" --post_name="silver-care" --post_status=draft
wp post create content/static-pages/silver-925-authenticity.md --post_type=page --post_title="اصالت نقره ۹۲۵" --post_name="silver-925-authenticity" --post_status=draft
wp post create content/static-pages/gemstones-guide.md --post_type=page --post_title="راهنمای سنگ‌های زینتی" --post_name="gemstones" --post_status=draft
```

---

## 5. Verification Required — List of Verified Created Page IDs (`جدول تأییدیه و شناسه واقعی صفحات ایجادشده`)

خروجی تأییدشدهٔ اجرای واقعی در استیجینگ (`wp post list --post_type=page --post_status=draft --fields=ID,post_title,post_name,post_status`):

| # | عنوان صفحه فارسی (`post_title`) | اسلاگ صفحه (`post_name` / Slug) | فایل مبدأ در مخزن | شناسه واقعی وردپرس (`Page ID`) | وضعیت انتشار (`post_status`) |
| :---: | :--- | :--- | :--- | :---: | :---: |
| 1 | **درباره رادمان** | `about-us` | `content/static-pages/about-us.md` | **`21`** | `draft` |
| 2 | **تماس با ما** | `contact-us` | `content/static-pages/contact-us.md` | **`22`** | `draft` |
| 3 | **سؤالات متداول** | `faq` | `content/static-pages/faq.md` | **`23`** | `draft` |
| 4 | **روش‌های ارسال** | `shipping` | `content/static-pages/shipping-policy.md` | **`24`** | `draft` |
| 5 | **شرایط بازگشت کالا** | `returns` | `content/static-pages/returns-policy.md` | **`25`** | `draft` |
| 6 | **حریم خصوصی** | `privacy-policy-radman` | `content/static-pages/privacy-policy.md` | **`26`** | `draft` |
| 7 | **قوانین و مقررات** | `terms` | `content/static-pages/terms-of-purchase.md` | **`27`** | `draft` |
| 8 | **راهنمای سایز انگشتر** | `ring-size-guide` | `content/static-pages/ring-size-guide.md` | **`28`** | `draft` |
| 9 | **راهنمای نگهداری نقره** | `silver-care` | `content/static-pages/silver-care-guide.md` | **`29`** | `draft` |
| 10 | **اصالت نقره ۹۲۵** | `silver-925-authenticity` | `content/static-pages/silver-925-authenticity.md` | **`30`** | `draft` |
| 11 | **راهنمای سنگ‌های زینتی** | `gemstones` | `content/static-pages/gemstones-guide.md` | **`31`** | `draft` |

- **صفحه اصلی فروشگاه (`Home Page`):** شناسه **`18`** (`Published` / `Static Front Page`)
- **تأییدیه فعال‌سازی قالب فرزند:** قالب فرزند `blocksy-child v1.0.0` با موفقیت فعال و استایل مشکی مات `#0B0B0E` و عاجی `#FAF7F2` اعمال شد.
- **تأییدیه واحد پول و عدم ایندکس:** واحد پول `IRT` (تومان ایران) و `blog_public = 0` تأیید شد.
- **عدم وجود اطلاعات حساس:** هیچ‌گونه رمز عبور، کلید API، توکن یا اطلاعات احراز هویتی در دستورات و اسکریپت‌های ایجادشده وجود ندارد.

---

## 6. Official Mission Status Statement (`اعلامیه رسمی وضعیت مأموریت`)
- **BRANDING AND CONTENT PROGRESS DOCUMENTED — NO SECRETS COMMITTED**
- **PR OPENED, NOT MERGED**
- **No token/auth method was changed**
- **Ready for reviewer approval**
