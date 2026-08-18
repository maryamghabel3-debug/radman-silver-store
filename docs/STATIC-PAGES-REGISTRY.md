# رجیستری صفحات استاتیک و وضعیت استقرار آن‌ها (`STATIC-PAGES-REGISTRY.md`)

> **رجیستری رسمی اسلاگ‌ها، شناسه‌های اولیه و وضعیت استقرار ۱۱ صفحه استاتیک رادمان سیلور ۹۲۵**
> *این سند بین «وضعیت فعلی واقعی در استیجینگ» و «وضعیت مطلوب پس از اجرای رانر ایمپورت» تمایز دقیق قائل می‌شود تا ادعای نادرستی در مورد ایمپورت کامل یا پاکسازی کامل ثبت نشود.*

---

## ۱. وضعیت فعلی واقعی در استیجینگ (2026-08-12)

- **محیط:** `https://staging.radmansilver.ir` (MizbanFa Mars plan, `blog_public = 0` / noindex).
- **زبان:** فارسی `fa_IR` فعال است.
- **پوسته:** `blocksy-child v1.0.0` با رنگ‌های مصوب `#0B0B0E` و `#FAF7F2` فعال است.
- **صفحه اصلی:** شناسه `18` به‌عنوان `static front page` تنظیم شده است.
- **صفحات ۲۱ تا ۳۱:** در حال حاضر صفحات **Draft placeholder** با عناوین موقت هستند که در حین bootstrap دستی اولیه ایجاد شده‌اند.
  - **متن روی میزبان (placeholder summary) هنوز با محتوای نهایی مخزن جایگزین نشده است.**
  - **متن منبع در مخزن (فایل‌های `content/static-pages/*.md`) کامل، بازبینی‌شده و placeholder-free است** (تأییدشده با `scripts/check_no_placeholders.py` و `scripts/test_plan_runner.sh`). همه تعهدهای عملیاتی تأییدنشده (ساعت کاری ثابت، پیک فعال تهران، پست/تیپاکس نهایی، SMS خودکار رهگیری، اقلام قطعی بسته، SLA ثابت بازپرداخت، پرداخت فعال، درگاه کاملاً تأییدشده) حذف و به‌صورت مشروط/پیش‌نویس بازنویسی شده‌اند.
  - **استقرار محتوا به‌صورت Draft روی استیجینگ PENDING است** (نیازمند مأموریت مصوب میزبانی) و از طریق `scripts/radman_stage_apply.sh --apply-staging` با `CONFIRM_STAGING_APPLY=YES` انجام می‌شود.
  - **انتشار عمومی (Publish) برای همه ۱۱ صفحه BLOCKED است** تا تأیید نهایی مالک (Owner approval) و بازبینی حقوقی (برای returns/privacy/terms). برای وضعیت لحظه‌ای تأییدها به [docs/STATIC-CONTENT-APPROVAL-REGISTRY.md](STATIC-CONTENT-APPROVAL-REGISTRY.md) مراجعه کنید.
  - استقرار نهایی از طریق رانر بازبینی‌شده و **idempotent** زیر انجام خواهد شد:
    - `scripts/radman_stage_apply.sh --plan` (حالت پیش‌فرض: dry-run)
    - `scripts/radman_stage_apply.sh --apply-staging` (فقط روی استیجینگ، با `CONFIRM_STAGING_APPLY=YES`)

### ۱.۱ Currency Safety Gate — دو وضعیت مجزا
برای اجتناب از ادعای نادرست، دروازهٔ ارز به دو گیت مستقل تقسیم شده است:

**A) Toman Core Storage/Display Gate — ✅ PASS**
- گزینهٔ پولی ووکامرس برابر `IRT` (تومان) مشاهده شده است.
- ورودی عددی `123456` در متاباکس قیمت به همان صورت `123456` ذخیره شده است.
- صفحهٔ محصول مقدار `123,456 Toman` را نمایش داده است.
- سبد خرید (cart) مقدار صحیح تومان را نمایش داده است.

**B) Payment/Schema Currency Gate — ⏳ PENDING**
- مجموع سبد در صفحهٔ checkout هنوز به‌صورت رسمی evidence نشده است.
- بازگشت (callback) درگاه پرداخت Gateland/Zarinpal تست نشده است.
- خروجی structured data / JSON-LD (Schema) برای واحد پول تست نشده است.
- خروجی واحد پول در فاکتور، سفارش و ایمیل‌ها تست نشده است.

**عبارت رسمی مورد استفاده در تمام اسناد:**
> *Toman direct input is verified for WooCommerce database storage, product display, and cart display. Payment, checkout, order, email, and Schema currency behavior remain PENDING and must pass before payment activation or production launch.*

### ۱.۲ پاکسازی صفحات تکراری — وضعیت واقعی
- **تأیید شده حذف شده:**
  - Page ID `2` (Sample Page پیش‌فرض وردپرس)
  - Page ID `3` (صفحه پیش‌فرض دیگر)
- **تأیید نشده / نیاز به بررسی روی میزبان:**
  - Page ID `10` با اسلاگ/محتوای `refund_returns`
  - **ثبت رسمی:** *"Page ID 10 cleanup status requires host verification."*
- ادعای «همهٔ صفحات تکراری پاکسازی شدند» در هیچ مستندی وجود ندارد.

---

## ۲. جدول رسمی اسلاگ‌ها و شناسه‌های اولیه

شناسه‌های زیر **در bootstrap دستی اولیه** ایجاد شده‌اند. در اجرای آتی رانر، رانر بر اساس **slug lookup** عمل می‌کند (update-by-slug) و هیچ‌گاه صفحه‌ای با اسلاگ تکراری ایجاد نخواهد کرد؛ اگر در زمان اجرا، صفحه‌ای با اسلاگ مشخص یافت نشود (مثلاً اگر حذف شده باشد)، آن را به‌صورت Draft ایجاد می‌کند.

| # | اسلاگ رسمی (`post_name`) | عنوان فارسی | فایل مبدأ Markdown | شناسه اولیه استیجینگ | وضعیت فعلی | وضعیت انتشار |
|:-:|:------------------------|:------------|:-------------------|:--------------------|:-----------|:------------|
| 1 | `about-us`               | درباره رادمان            | `content/static-pages/about-us.md`              | `21` | Draft placeholder (bootstrap) | `draft` |
| 2 | `contact-us`             | تماس با ما               | `content/static-pages/contact-us.md`            | `22` | Draft placeholder (bootstrap) | `draft` |
| 3 | `faq`                    | سؤالات متداول            | `content/static-pages/faq.md`                   | `23` | Draft placeholder (bootstrap) | `draft` |
| 4 | `shipping`               | روش‌های ارسال            | `content/static-pages/shipping-policy.md`       | `24` | Draft placeholder (bootstrap) | `draft` |
| 5 | `returns`                | شرایط بازگشت کالا        | `content/static-pages/returns-policy.md`        | `25` | Draft placeholder (bootstrap) | `draft` |
| 6 | `privacy-policy-radman`  | حریم خصوصی              | `content/static-pages/privacy-policy.md`        | `26` | Draft placeholder (bootstrap) | `draft` |
| 7 | `terms`                  | قوانین و مقررات          | `content/static-pages/terms-of-purchase.md`     | `27` | Draft placeholder (bootstrap) | `draft` |
| 8 | `ring-size-guide`        | راهنمای سایز انگشتر      | `content/static-pages/ring-size-guide.md`       | `28` | Draft placeholder (bootstrap) | `draft` |
| 9 | `silver-care`            | راهنمای نگهداری نقره     | `content/static-pages/silver-care-guide.md`     | `29` | Draft placeholder (bootstrap) | `draft` |
| 10| `silver-925-authenticity`| اصالت نقره ۹۲۵           | `content/static-pages/silver-925-authenticity.md`| `30` | Draft placeholder (bootstrap) | `draft` |
| 11| `gemstones`              | راهنمای سنگ‌های زینتی    | `content/static-pages/gemstones-guide.md`       | `31` | Draft placeholder (bootstrap) | `draft` |

**صفحه اصلی (Home):** شناسه `18` — منتشر شده و به‌عنوان `front page` تنظیم است (توسط رانر ایمپورت تغییر داده نمی‌شود).

---

## ۳. Idempotency Strategy برای ایمپورت آتی

1. رانر `scripts/render_static_pages.py` فقط بخش `## Content` هر فایل Markdown را به HTML امن تبدیل می‌کند و بخش‌های داخلی (`SEO`, `Page Purpose`, `Trust Notes`, `Owner Fill Later`, `Internal Link Suggestions`) را **هرگز** در محتوای صفحه قرار نمی‌دهد.
2. برای هر اسلاگ رسمی، رانر با `wp post list --post_name__in=<slug>` صفحهٔ موجود را پیدا می‌کند:
   - **اگر موجود بود:** `wp post update <ID>` روی همان شناسه (همواره `--post_status=draft`).
   - **اگر موجود نبود:** `wp post create` با همان اسلاگ (همواره `--post_status=draft`).
3. قبل از هر تغییر، بک‌آپ DB و پوشهٔ child theme در `RADMAN_PRIVATE_DIR/backups/` (خارج از وب‌روت، `chmod 600`) گرفته می‌شود.
4. قفل `flock` از اجرای هم‌زمان دو استقرار جلوگیری می‌کند.
5. **هیچ صفحه‌ای به‌صورت خودکار publish نمی‌شود. همه صفحات Draft باقی می‌مانند تا مأموریت انتشار جداگانه‌ای مصوب شود.**

---

## ۴. خلاصه وضعیت رسمی

- ✅ زبان فارسی `fa_IR` فعال.
- ✅ `blocksy-child` فعال روی استیجینگ.
- ⏳ شناسه‌های `21–31` روی میزبان **placeholder** باقی مانده‌اند و استقرار محتوای کامل مخزن **PENDING** است.
- ✅ **Plan runs cleanly:** رانر `scripts/radman_stage_apply.sh --plan` (باگ `/dev/fd` جیل‌شل قبلی رفع شده) جدول DEPLOY PLAN را چاپ می‌کند و روی همه ۱۱ صفحه placeholder = no گزارش می‌دهد.
- ✅ **Repo content placeholder-free:** همه ۱۱ فایل Markdown در `content/static-pages/` از نظر gate عبور می‌کنند (تست رگرسیون برای بیضی عادی `…` PASS، برای `[…]` و کلاس `radman-placeholder` FAIL).
- ✅ **Draft deployment readiness:** محتوا از نظر فنی آمادهٔ استقرار به‌صورت Draft روی استیجینگ است.
- ⏳ **Host deployment:** اجرای `--apply-staging` روی میزبان PENDING (نیازمند مأموریت مصوب میزبانی).
- ⏳ **Owner approval:** تأیید نهایی مالک برای محتوای تمام ۱۱ صفحه PENDING است.
- ⏳ **Legal approval:** بازبینی حقوقی برای صفحات `returns`، `privacy-policy-radman` و `terms` PENDING است.
- 🚫 **Publication BLOCKED:** هیچ‌یک از صفحات تا تأیید نهایی مالک/حقوقی منتشر نخواهند شد.
- ⚠️ شناسه‌های `2` و `3` تأیید شده حذف شده‌اند؛ شناسه `10` نیازمند بررسی روی میزبان است.
- ✅ گیت A ارز (ذخیره‌سازی/نمایش محصول/سبد خرید بر حسب تومان) **PASS**.
- ⏳ گیت B ارز (پرداخت/چک‌اوت/ایمیل/Schema) **PENDING**.
- ⏳ راه‌اندازی Host Operations Agent Access **PENDING** (مراجعه شود به [HOST-OPS-AGENT-ACCESS.md](HOST-OPS-AGENT-ACCESS.md)).
- 🔒 پروداکشن (`public_html`) دست‌نخورده باقی مانده است.
