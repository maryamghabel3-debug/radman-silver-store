# SEO Topic Map Contract — Future Web-Enabled Research Agent

این قرارداد فقط schema خروجی یک مأموریت تحقیقاتی بعدی را تعریف می‌کند. PR-34 هیچ keyword volume، competitor traffic یا market evidence ساختگی تولید نمی‌کند.

## Required output columns

| Field | Contract |
|---|---|
| `keyword` | عبارت واقعی مشاهده‌شده در منبع research |
| `search_intent` | informational / commercial / transactional / navigational |
| `topic_cluster` | خوشه موضوعی قابل ردیابی |
| `page_type` | product / category / guide / FAQ / landing |
| `priority` | rule-based priority همراه reason |
| `internal_link_targets` | URLهای داخلی پیشنهادی |
| `competitor_urls` | فقط URL واقعی بررسی‌شده |
| `content_gap` | gap مبتنی بر evidence |
| `funnel_stage` | awareness / consideration / conversion / retention |
| `recommended_cta` | CTA متناسب با intent و policy |
| `schema_type` | schema مناسب، بدون تداخل با Product schema Woo/Rank Math |

## Evidence rules

- هر keyword/competitor claim باید source URL و timestamp داشته باشد.
- volume، CPC، traffic یا ranking بدون داده واقعی باید خالی بماند، نه تخمین زده شود.
- aggregateRating/review، shipping، return و warranty schema بدون داده/policy تأییدشده ممنوع است.
- Product/Offer schema فروشگاه توسط WooCommerce/Rank Math مدیریت می‌شود؛ agent نباید implementation دوم تزریق کند.
- خروجی research فقط recommendation است و publication یا content overwrite انجام نمی‌دهد.

## Suggested formats

CSV و JSON private با schema version، generated timestamp، evidence URL و confidence/review status. اجرای research نیازمند web-enabled mission جداگانه و تأیید مالک است.
