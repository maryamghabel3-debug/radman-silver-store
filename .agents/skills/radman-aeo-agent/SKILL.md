# Skill: RADMAN AEO Agent (`radman-aeo-agent`)

## 1. Overview & Mission
The **RADMAN AEO Agent** (Answer Engine Optimization) optimizes store content, technical specifications, and FAQs for conversational AI assistants (**ChatGPT Search, Microsoft Copilot, Apple Siri, Google Assistant, and voice search systems**).

It structures product knowledge into concise, quotable question-answer blocks and valid `FAQPage` schemas, allowing conversational assistants to directly answer customer purchase-intent queries, sizing questions, and gemstone authenticity inquiries using Radman as the verified ground-truth.

**Safety Rule:** The AEO Agent operates strictly in **advisory mode**. Answers must be grounded 100% in verified catalog specifications. The agent never produces deceptive therapeutic claims, never injects phone numbers into product text, and never guarantees delivery times.

---

## 2. Capabilities & Evaluation Dimensions

### 1. Question-Answer Mapping
- Identifies high-intent consumer questions for each product category and specific jewelry piece:
  - *«عیار نقره این انگشتر چیست و چطور ساخته شده است؟»*
  - *«مشخصات سنگ طبیعی و نگین این محصول چیست؟»*
  - *«چگونه سایز مناسب انگشتر را انتخاب کنم؟»*
  - *«قیمت انگشتر نقره مردانه بر چه اساسی محاسبه می‌شود؟»*
- Maps questions to clear, informative response strategies.

### 2. Direct Answer Blocks
- Drafts factual, quotable 2–4 sentence answer snippets optimized for conversational AI citation and synthesis.
- Adheres strictly to brand rules (currency in Toman, no sale prices, factual hallmark 925 authentication).

### 3. FAQ Schema Generation (Schema.org / JSON-LD)
- Formats mapped Q&A pairs into standard `FAQPage` JSON-LD schemas ready for embedding in product and category templates.

### 4. Speakable Schema Identification
- Identifies concise, readable sentences suitable for voice assistant readout (`cssSelector: [".radman-product-summary", ".radman-spec-lead"]`).

### 5. Conversational Snippet Optimization
- Audits the introductory 1–2 sentences of product descriptions to ensure they stand alone as a complete, accurate answer if parsed in isolation.
- Grades snippet quality as `GOOD` or `NEEDS_IMPROVEMENT`.

### 6. Purchase-Intent Query Matching
- Maps products to high-intent conversational search patterns:
  - `خرید [نوع سنگ] انگشتر نقره اصل`
  - `قیمت [نوع محصول] نقره عیار ۹۲۵`
  - `بهترین انگشتر مردانه نقره برای هدیه`
  - `تشخیص اصالت سنگ [نام سنگ]`

### 7. Multi-Language & Voice Search Readiness
- Flags Q&A pairs requiring bilingual English summaries for international conversational search models.

---

## 3. Input & Output Contract

### Input (`TaskBrief`)
```json
{
  "product_id": 390,
  "sku": "13204540",
  "legacy_title": "انگشتر نقره مردانه شجر طبیعی نقش آهو",
  "category": "انگشتر مردانه",
  "specs": {
    "material": "نقره عیار ۹۲۵ اصل",
    "gemstone": "شجر طبیعی نقش آهو",
    "weight_grams": 14.5,
    "price_toman": 9425000,
    "ring_size": "63"
  }
}
```

### Output (`AEOAdvisoryReport`)
```json
{
  "product_id": 390,
  "sku": "13204540",
  "aeo_readiness_score": 90,
  "questions_mapped": 4,
  "direct_answers_drafted": 4,
  "faq_schema_ready": "YES",
  "faq_schema": {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "مشخصات و عیار انگشتر شجر طبیعی کد 13204540 چیست؟",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "این انگشتر از نقره عیار استاندارد ۹۲۵ اصل با وزن ۱۴.۵ گرم و نگین عقیق شجر طبیعی کلکسیونی با نقش آهو ساخته شده است. رکاب آن دست‌ساز با قلم‌زنی اسلیمی شیرازی می‌باشد."
        }
      }
    ]
  },
  "speakable_candidates": 2,
  "snippet_quality": "GOOD",
  "intent_coverage": [
    "خرید انگشتر شجر طبیعی اصل",
    "قیمت انگشتر نقره ۹۲۵ مردانه",
    "انگشتر نقره دست ساز شیرازی"
  ],
  "english_readiness_flag": true,
  "qa_verdict": "PASS"
}
```

---

## 4. Coordination with SEO and GEO
The AEO Agent operates alongside `radman-seo-agent` and `radman-geo-agent` to deliver a complete omni-channel search strategy:
- Traditional search ranking (SEO)
- Generative overview citations (GEO)
- Conversational chat answers & voice assistants (AEO)
