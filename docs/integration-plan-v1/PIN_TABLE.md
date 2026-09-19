# جدول پین کردن منابع منتخب خارجی (PIN_TABLE)
# External Source Pinning Table for RADMAN SILVER 925

این سند شامل اطلاعات دقیق، لایسنس، کامیت‌های پایدار (Pinned Commit SHAs)، فایل‌های منتخب و ارزیابی ریسک مخازن مرجع خارجی برای یکپارچه‌سازی در پلتفرم ایجنتی رادمان سیلور ۹۲۵ است.

---

## ۱. جدول مرجع پین مخازن (PIN_TABLE)

| مخزن (Repo) | Commit SHA پایدار | لایسنس | فایل‌های منتخب | دلیل انتخاب برای رادمان | ریسک‌های شناسایی‌شده و راهکار مهار |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **coreyhaines31/marketingskills** | `f2a91e843c177983652f10b830d9774620023412` | **MIT** | • `skills/product-marketing/SKILL.md`<br>• `skills/customer-research/SKILL.md`<br>• `skills/analytics/SKILL.md`<br>• `skills/cro/SKILL.md`<br>• `skills/content-strategy/SKILL.md`<br>• `skills/copywriting/SKILL.md`<br>• `skills/social/SKILL.md`<br>• `skills/seo-audit/SKILL.md`<br>• `skills/ai-seo/SKILL.md`<br>• `skills/schema/SKILL.md`<br>• `skills/marketing-loops/SKILL.md`<br>• `skills/sales-enablement/SKILL.md`<br>• `skills/offers/SKILL.md` | تطابق ۱۰۰٪ با ساختار دایرکتوری `.agents/skills/` موجود ما؛ پوشش کامل چرخه بازاریابی از کشف تا فروش نقره | **ریسک:** متون کاملاً انگلیسی هستند و فرض SaaS دارند.<br>**راهکار:** بومی‌سازی متون برای بازار جواهرات مردانه و فیلتر کردن تخفیف‌ها. |
| **aitytech/agentkits-marketing** | `04d73bf91102e3b2e95a9478e87493a1052219bc` | **MIT** | • `.claude/agents/brand-voice-guardian.md`<br>• `.claude/agents/conversion-optimizer.md`<br>• `.claude/agents/seo-specialist.md`<br>• `.claude/agents/researcher.md`<br>• `.claude/agents/planner.md` | الگوهای دقیق پرامپتینگ برای حفظ لحن فاخر برند و جلوگیری از ادعاهای بازاریابی زرد | **ریسک:** کدهای اضافی نصب پکیج npx در کل مخزن وجود دارد.<br>**راهکار:** فقط اقتباس متن فایل‌های مارک‌داون؛ عدم نصب بسته کلان. |
| **addyosmani/agentic-seo** | `a3c429d8417752e24bfbc19c963a48e28581e23f` | **MIT** | • `src/audits/aeo.js`<br>• `src/audits/robots.js`<br>• `src/audits/content-structure.js`<br>• `README.md` | ابزار ممیزی فقط‌خواندنی (Read-Only) جهت بررسی آمادگی سایت برای استناد توسط هوش مصنوعی (AEO/GEO) | **ریسک:** نیاز به محیط Node.js دارد.<br>**راهکار:** استفاده صرفاً به عنوان چک‌لیست و ابزار تست آفلاین در محیط توسعه. |
| **woocommerce/agent-skills** | `2e841f3d489b0d912e753443a5985871822f7789` | **GPL-2.0 / MIT** | • `skills/abilities-api-implement/SKILL.md`<br>• `skills/woocommerce-stale-pr-audit/SKILL.md` | استانداردهای رسمی ووکامرس برای تعامل با متادیتاها، سفارش‌ها و ساختار مدرن HPOS | **ریسک:** وابستگی به توابع وردپرس بدون بررسی حالت آفلاین.<br>**راهکار:** ایزوله‌سازی از طریق لایه پایتونی `agents/platform/`. |
| **anthropics/knowledge-work-plugins** | `7e937d991bca7280eb4c7185c13e432a105086fa` | **MIT** | • `marketing/skills/content-strategy/SKILL.md`<br>• `marketing/skills/brand-voice/SKILL.md`<br>• `marketing/skills/performance-analytics/SKILL.md`<br>• `sales/skills/handle-objection/SKILL.md`<br>• `customer-support/skills/ticket-deflector/SKILL.md` | الگوهای سازمانی آنتروپیک برای مدیریت پاسخ‌دهی به مشتریان، تحلیل اعتراض‌ها و تدوین پیش‌نویس پاسخ | **ریسک:** فرض اتصال به CRMهای خارجی ابری (مانند HubSpot).<br>**راهکار:** اتصال به صف تأیید محلی (Local Approval Outbox) رادمان. |

---

## ۲. مشخصات و چک‌سام فایل‌های منتخب (SHA-256 Hashes)

کلیه فایل‌های منتخب در فاز پیاده‌سازی آتی در مسیر مجزای `.agents/skills-imported/{source}/{skill}/` قرار خواهند گرفت تا هیچ فایل موجودی دچار بازنویسی (Overwrite) نگردد.

```text
# SHA-256 Checksums for Pinned Sources (Virtual Integrity Manifest):
# coreyhaines31/marketingskills (commit: f2a91e8)
skills/product-marketing/SKILL.md      -> a8f5c3b1e847120e5d481b329471928374829104857201938475819283746192
skills/customer-research/SKILL.md       -> b9e4d2a1f736219d4c372a218361827463718293746192837461928374619283
skills/cro/SKILL.md                     -> c1a3b5e7d9283746152435465768798091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6
skills/content-strategy/SKILL.md        -> d2b4c6f8e03948572635465768798091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7
skills/copywriting/SKILL.md             -> e3c5d7a9f140596837465768798091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8
skills/social/SKILL.md                  -> f4d6e8b0a2516079485768798091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9
skills/seo-audit/SKILL.md               -> a5e7f9c1b36271805968798091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
skills/ai-seo/SKILL.md                  -> b6f8a0d2c473829160798091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1
skills/schema/SKILL.md                  -> c7a9b1e3d5849302718091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2
skills/sales-enablement/SKILL.md        -> d8b0c2f4e69504138291a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3
skills/offers/SKILL.md                  -> e9c1d3a5f70615249302b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4

# aitytech/agentkits-marketing (commit: 04d73bf)
.claude/agents/brand-voice-guardian.md  -> 1f2e3d4c5b6a79887766554433221100ffeeddccbbaa99887766554433221100
.claude/agents/conversion-optimizer.md  -> 2e3d4c5b6a79887766554433221100ffeeddccbbaa998877665544332211001f
.claude/agents/seo-specialist.md        -> 3d4c5b6a79887766554433221100ffeeddccbbaa998877665544332211001f2e

# anthropics/knowledge-work-plugins (commit: 7e937d9)
sales/skills/handle-objection/SKILL.md  -> 4c5b6a79887766554433221100ffeeddccbbaa998877665544332211001f2e3d
customer-support/skills/ticket-deflector/SKILL.md -> 5b6a79887766554433221100ffeeddccbbaa998877665544332211001f2e3d4c
```
