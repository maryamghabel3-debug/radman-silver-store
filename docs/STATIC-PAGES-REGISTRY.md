# رجیستری صفحات استاتیک و پیش‌نویس‌های استیجینگ رادمان سیلور (`STATIC-PAGES-REGISTRY.md`)

> **رجیستری رسمی شناسه‌ها (Page IDs) و اسلاگ‌های صفحات استاتیک رادمان سیلور ۹۲۵ در وردپرس استیجینگ**  
> *این سند مشخصات واقعی و تأییدشدهٔ ۱۱ صفحه استاتیک پیش‌نویس (`Draft`)، صفحه اصلی زنده (`Front Page` ID 18) و وضعیت فعال‌سازی قالب فرزند `blocksy-child` و زبان فارسی `fa_IR` در سرور استیجینگ (`https://staging.radmansilver.ir`) را جهت استفاده در ساخت منوی اصلی ثبت می‌کند. استقرار رایدلین اکیداً خارج از محدوده است.*

---

## 1. Verified Real Results (from Owner's Actual Staging Terminal Execution)

- **Date:** `2026-08-12` (`Asia/Tehran` timezone)
- **Host / Environment:** MizbanFa Mars plan staging (`https://staging.radmansilver.ir`)
- **Persian Language (`fa_IR`):** Active and confirmed (`wp option get WPLANG = fa_IR`)
- **Child Theme:** Created and activated: **`blocksy-child v1.0.0`** (confirmed via `wp theme list`)
- **Child Theme Brand Colors:**
  - `style.css`: Body background `#0B0B0E` (مشکی مات اشرافی), Text color `#FAF7F2` (عاجی درخشان)
  - `functions.php`: Enqueues parent (`blocksy`) + child (`blocksy-child`) styles correctly
- **Static Front Page (Home Page):**
  - Published and set as static front page: **Home page (ID `18`)** (`https://staging.radmansilver.ir`)
- **Duplicate / Sample Pages Cleanup:**
  - Duplicate/default pages removed by owner: `sample page`, `duplicate refund policy`, `duplicate privacy policy`
- **Search Engine Indexing (`noindex`):**
  - `blog_public = 0` (`noindex confirmed, still active`)
- **WooCommerce Currency & Safety Gate:**
  - **`IRT` (Iranian Toman / تومان ایران):** WooCommerce currency displays as `IRT` — confirmed correct per **Currency Safety Gate** testing (`Toman direct input is verified as correct; Currency Safety Gate CLOSED`).

---

## 2. Official Registry of 11 Static Persian Pages (`جدول شناسه‌ها و اسلاگ‌های ۱۱ صفحه استاتیک`)

تمامی ۱۱ صفحه استاتیک زیر از روی فایل‌های محتوایی پوشه `content/static-pages/` با وضعیت پیش‌نویس (`Draft`) در وردپرس استیجینگ رادمان سیلور ایجاد شده‌اند:

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

---

## 3. Summary of Verified Core Pages & Menu Structure (`خلاصه صفحات اصلی سایت`)

- **صفحه اصلی فروشگاه (`Home Page`):** شناسه **`18`** (`Published` / `Static Front Page`)
- **صفحات راهنمای خرید و قوانین (پیش‌نویس):** شناسه‌های **`21` تا `31`** (مطابق جدول فوق جهت افزودن به منوی اصلی هدر و فوتر پس از انتشار نهایی)
- **پاکسازی صفحات اضافی:** تمامی صفحات پیش‌فرض وردپرس و نسخه‌های تکراری (Sample Page، Refund Policy تکراری و Privacy Policy تکراری) حذف شدند.
- **امنیت و محرمانگی:** هیچ‌گونه رمز عبور، کلید API، توکن یا اطلاعات احراز هویتی در این سند و مخزن نگهداری نمی‌شود.

---

## 4. Official Mission Status Statement (`اعلامیه رسمی وضعیت مأموریت`)
- **BRANDING AND CONTENT PROGRESS DOCUMENTED — NO SECRETS COMMITTED**
- **PR OPENED, NOT MERGED**
- **No token/auth method was changed**
- **Ready for reviewer approval**
