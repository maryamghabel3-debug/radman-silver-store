# قوانین قیمت‌گذاری و محاسبه اجرت نقره (`PRICING-RULES.md`)

This document defines the mathematical pricing formulas, daily silver rate verification protocols, and Toman presentation rules for **RADMAN SILVER 925**.

---

## 1. Mathematical Pricing Formula (`فرمول محاسبه قیمت فروش`)

All retail silver jewelry prices in `radman-silver-store` are calculated using the following deterministic formula:

```text
Retail_Price_IRR = (Daily_Silver_925_Gram_Rate_IRR * Net_Weight_Grams) + Gemstone_Cost_IRR + Craftsmanship_Fee_IRR + Packaging_Fee_IRR + Profit_Margin_IRR
```

### Formula Variable Definitions
- **`Daily_Silver_925_Gram_Rate_IRR`:** Live 925 sterling silver rate in Iranian Rials per gram, queried daily at 10:30 AM Tehran time.
- **`Net_Weight_Grams`:** Verified silver metal weight (`e.g., 5.40 grams`).
- **`Gemstone_Cost_IRR`:** Fixed cost of gemstone (`e.g., Agate, Turquoise, Zirconia`); `0` for plain silver items.
- **`Craftsmanship_Fee_IRR`:** Fixed silversmithing craftsmanship fee per gram (`اجرت ساخت`).
- **`Packaging_Fee_IRR`:** Fixed cost of luxury gift box and authenticity certificate (`e.g., 150,000 Toman`).
- **`Profit_Margin_IRR`:** Retail brand markup percentage (`e.g., 25%`).

---

## 2. Daily Market Rate Verification Protocol (`تأیید روزانه نرخ نقره`)

1. At **10:30 AM Tehran time**, `Agent-Pricing` fetches the daily silver gram rate from primary Tehran market API.
2. If the price variance compared to yesterday is **> 3%**, `Agent-Pricing` marks the alert as **HIGH VOLATILITY (`نوسان شدید بازار`)** in Telegram.
3. No price update is pushed to WooCommerce until the owner clicks `[تأیید و اعمال قیمت امروز]` in Telegram.
4. If the owner clicks `[لغو و تنظیم دستی]`, they can enter a custom gram rate using command `/price 85000`.

---

## 3. Rounding & Currency Display Rules (`قوانین گرد کردن و نمایش تومان`)

- **Internal Database Currency:** All prices stored in WooCommerce database in **Iranian Rials (`IRR`)** to prevent payment gateway truncation errors.
- **Storefront Display Currency:** Displayed to customers in **Toman (`تومان`)** via Persian WooCommerce localization (`1 Toman = 10 IRR`).
- **Luxury Rounding Standard:**
  - All retail prices are rounded up to the nearest **10,000 Toman (`100,000 IRR`)** for clean luxury presentation.
  - Example: Calculated price `2,483,200 Toman` -> Displayed as **`۲,۴۹۰,۰۰۰ تومان`**.
