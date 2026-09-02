# Skill: RADMAN SEO Agent (`radman-seo-agent`)

## 1. Overview & Mission
The **RADMAN SEO Agent** specializes in luxury Persian e-commerce search engine optimization and AI visibility for **RADMAN SILVER 925**.

It generates search-optimized, brand-compliant product titles, Persian meta descriptions, focus keywords, and Rank Math SEO metadata contracts. It ensures high search visibility for queries related to 925 sterling silver jewelry and authentic natural gemstones while strictly preventing keyword stuffing, duplicate content, and false marketing claims.

**Safety Rule:** This skill *never* publishes products or alters live search configurations directly. All outputs are generated as structured proposal manifests awaiting QA and owner sign-off.

---

## 2. Capabilities
- **Persian Luxury SEO Titles:** Formats titles matching the proven standard:  
  `[نام تمیز محصول] | خرید [نوع محصول] نقره ۹۲۵ اصل | رادمان سیلور`
- **Persian Meta Descriptions:** Crafts persuasive, luxury-tone meta descriptions between 130–160 characters highlighting authentic 925 hallmark, craftsmanship, and gemstone purity.
- **Rank Math Metadata Contract:** Emits structured JSON compatible with Rank Math SEO WordPress fields (`rank_math_title`, `rank_math_description`, `rank_math_focus_keyword`, `rank_math_robots`).
- **Keyword Stuffing & Repetition Checks:** Analyzes keyword density to prevent search engine penalties.
- **Duplicate Content Audit:** Cross-references proposed descriptions against existing catalog archives to guarantee uniqueness.
- **Search Console Readiness:** Verifies canonical URL format, schema markup, and Persian slug validity.

---

## 3. Integration with Standalone Agents
This skill wraps and extends the deterministic logic from:
- `agents/agent_product_seo.py` (Title and meta generator)
- `agents/agent_product_seo_qa.py` (Pre-publication SEO quality gate)

---

## 4. Input & Output Contract

### Input
```json
{
  "product_id": 65,
  "clean_title": "انگشتر مردانه نقره ۹۲۵ عقیق سرخ یمنی",
  "category": "انگشتر مردانه",
  "specs": {
    "silver_hallmark": "925",
    "gemstone": "عقیق سرخ یمنی اصل",
    "weight_grams": 11.2,
    "ring_size": "62"
  }
}
```

### Output
```json
{
  "product_id": 65,
  "seo_title": "انگشتر مردانه نقره ۹۲۵ عقیق سرخ یمنی | خرید انگشتر مردانه نقره ۹۲۵ اصل | رادمان سیلور",
  "meta_description": "خرید انگشتر مردانه نقره ۹۲5 عقیق سرخ یمنی اصل با عیار استاندارد ۹۲۵، نگین طبیعی و رکاب دست‌ساز فاخر در گالری رادمان سیلور. ارسال با بسته‌بندی نفیس.",
  "focus_keyword": "انگشتر مردانه نقره عقیق سرخ یمنی",
  "rank_math_meta": {
    "rank_math_title": "انگشتر مردانه نقره ۹۲۵ عقیق سرخ یمنی | خرید انگشتر مردانه نقره ۹۲۵ اصل | رادمان سیلور",
    "rank_math_description": "خرید انگشتر مردانه نقره ۹۲5 عقیق سرخ یمنی اصل با عیار استاندارد ۹۲۵، نگین طبیعی و رکاب دست‌ساز فاخر در گالری رادمان سیلور. ارسال با بسته‌بندی نفیس.",
    "rank_math_focus_keyword": "انگشتر مردانه نقره عقیق سرخ یمنی",
    "rank_math_robots": ["index", "follow"]
  },
  "keyword_density_percent": 2.4,
  "duplicate_risk_score": 0.0,
  "qa_status": "SEO_PASS"
}
```

---

## 5. Sample Task Brief
```markdown
# Task Brief: SEO Optimization for Ring 65
- Skill: radman-seo-agent
- Objective: Generate luxury Persian SEO title, description, and Rank Math schema for Men's Yemeni Carnelian Silver Ring
- Constraints: No phone numbers, no shipping promises, character count within 130-160
```
