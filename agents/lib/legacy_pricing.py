"""Gemstone-aware legacy price-floor rules for RADMAN SILVER.

All monetary values are Toman. This module intentionally contains no Rial/Toman
conversion and uses Decimal for every pricing calculation.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from typing import Any, Dict, Optional, Tuple

STANDARD_RATE_TOMAN_PER_GRAM = 650_000
LARGE_STONE_RATE_TOMAN_PER_GRAM = 590_000
ROUNDING_STEP_TOMAN = 50_000
LARGE_STONE_MIN_CONFIDENCE = Decimal("0.85")
MIN_PLAUSIBLE_LEGACY_PRICE_TOMAN = 50_000
MAX_PLAUSIBLE_LEGACY_PRICE_TOMAN = 10_000_000_000
MAX_PLAUSIBLE_WEIGHT_GRAMS = Decimal("500")

SELECTION_REASONS = {
    "LEGACY_PRICE_HIGHER",
    "CALCULATED_FLOOR_HIGHER",
    "EQUAL",
    "LEGACY_MISSING_USED_CALCULATED",
    "WEIGHT_MISSING_USED_LEGACY_REVIEW",
    "INVALID_DATA_REVIEW",
}

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


@dataclass(frozen=True)
class PricingResult:
    category: str
    requested_stone_class: str
    effective_stone_class: str
    stone_confidence: Decimal
    rate_toman_per_gram: int
    weight_grams: Optional[Decimal]
    legacy_price_toman: Optional[int]
    calculated_raw_toman: Optional[Decimal]
    calculated_price_toman: Optional[int]
    selected_pre_round_toman: Optional[int]
    final_price_toman: Optional[int]
    selection_reason: str
    requires_review: bool
    warnings: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        for key in ("stone_confidence", "weight_grams", "calculated_raw_toman"):
            if value[key] is not None:
                value[key] = format(value[key], "f")
        value["warnings"] = list(self.warnings)
        return value


def _clean_numeric(value: Any) -> str:
    return (
        str(value if value is not None else "")
        .strip()
        .translate(_DIGITS)
        .replace("٬", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("٫", ".")
        .replace("تومان", "")
    )


def parse_toman(value: Any) -> Optional[int]:
    """Parse localized Toman digits exactly; never multiply or divide by ten."""
    cleaned = _clean_numeric(value)
    if not cleaned:
        return None
    if not re.fullmatch(r"[0-9]+", cleaned):
        return None
    parsed = int(cleaned)
    if not (
        MIN_PLAUSIBLE_LEGACY_PRICE_TOMAN
        <= parsed
        <= MAX_PLAUSIBLE_LEGACY_PRICE_TOMAN
    ):
        return None
    return parsed


def parse_weight_grams(value: Any) -> Optional[Decimal]:
    cleaned = _clean_numeric(value)
    if not cleaned:
        return None
    try:
        parsed = Decimal(cleaned)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed <= 0 or parsed > MAX_PLAUSIBLE_WEIGHT_GRAMS:
        return None
    return parsed


def parse_confidence(value: Any) -> Decimal:
    try:
        confidence = Decimal(str(value))
    except InvalidOperation:
        return Decimal("0")
    if not confidence.is_finite():
        return Decimal("0")
    return min(Decimal("1"), max(Decimal("0"), confidence))


def round_up_toman(value: Decimal, step: int = ROUNDING_STEP_TOMAN) -> int:
    if value < 0:
        raise ValueError("price cannot be negative")
    units = (value / Decimal(step)).to_integral_value(rounding=ROUND_CEILING)
    return int(units * Decimal(step))


def choose_rate(
    category: str,
    stone_class: str,
    confidence: Any,
) -> Tuple[int, str, bool, Tuple[str, ...]]:
    category = str(category or "").strip().lower()
    requested = str(stone_class or "uncertain").strip().lower()
    conf = parse_confidence(confidence)
    warnings = []
    requires_review = False

    if category not in {"rings", "necklaces", "bracelets"}:
        warnings.append("unsupported or missing category")
        return STANDARD_RATE_TOMAN_PER_GRAM, "uncertain", True, tuple(warnings)

    if category != "rings":
        return STANDARD_RATE_TOMAN_PER_GRAM, "not_applicable", False, tuple()

    if requested == "large_stone":
        if conf >= LARGE_STONE_MIN_CONFIDENCE:
            return LARGE_STONE_RATE_TOMAN_PER_GRAM, "large_stone", False, tuple()
        warnings.append("large-stone confidence below 0.85; higher rate enforced")
        return STANDARD_RATE_TOMAN_PER_GRAM, "uncertain", True, tuple(warnings)

    if requested in {"no_stone", "small_stone"}:
        return STANDARD_RATE_TOMAN_PER_GRAM, requested, False, tuple()

    warnings.append("stone size uncertain; higher rate enforced")
    requires_review = True
    return STANDARD_RATE_TOMAN_PER_GRAM, "uncertain", requires_review, tuple(warnings)


def calculate_safe_price(
    *,
    category: str,
    stone_class: str,
    stone_confidence: Any,
    weight_grams: Any,
    legacy_price_toman: Any,
) -> PricingResult:
    confidence = parse_confidence(stone_confidence)
    rate, effective_class, rate_review, rate_warnings = choose_rate(
        category, stone_class, confidence
    )
    warnings = list(rate_warnings)
    weight = parse_weight_grams(weight_grams)
    legacy = parse_toman(legacy_price_toman)
    requires_review = rate_review

    raw_weight_present = str(weight_grams if weight_grams is not None else "").strip()
    raw_legacy_present = str(
        legacy_price_toman if legacy_price_toman is not None else ""
    ).strip()
    if raw_weight_present and weight is None:
        warnings.append("weight is missing or implausible")
        requires_review = True
    if raw_legacy_present and legacy is None:
        warnings.append("legacy Toman price is missing or implausible")
        requires_review = True

    calculated_raw: Optional[Decimal] = None
    calculated_integer: Optional[int] = None
    if weight is not None:
        calculated_raw = weight * Decimal(rate)
        calculated_integer = int(
            calculated_raw.to_integral_value(rounding=ROUND_CEILING)
        )

    selected: Optional[Decimal]
    if legacy is not None and calculated_raw is not None:
        legacy_decimal = Decimal(legacy)
        if legacy_decimal > calculated_raw:
            selected = legacy_decimal
            reason = "LEGACY_PRICE_HIGHER"
        elif calculated_raw > legacy_decimal:
            selected = calculated_raw
            reason = "CALCULATED_FLOOR_HIGHER"
        else:
            selected = legacy_decimal
            reason = "EQUAL"
    elif legacy is None and calculated_raw is not None:
        selected = calculated_raw
        reason = "LEGACY_MISSING_USED_CALCULATED"
        requires_review = True
        warnings.append("legacy price unavailable; calculated floor used")
    elif legacy is not None and calculated_raw is None:
        selected = Decimal(legacy)
        reason = "WEIGHT_MISSING_USED_LEGACY_REVIEW"
        requires_review = True
        warnings.append("weight unavailable; legacy price retained for review")
    else:
        selected = None
        reason = "INVALID_DATA_REVIEW"
        requires_review = True
        warnings.append("neither a valid weight nor a valid legacy Toman price exists")

    selected_integer = (
        int(selected.to_integral_value(rounding=ROUND_CEILING))
        if selected is not None
        else None
    )
    final_price = round_up_toman(selected) if selected is not None else None

    return PricingResult(
        category=str(category or "").strip().lower(),
        requested_stone_class=str(stone_class or "uncertain").strip().lower(),
        effective_stone_class=effective_class,
        stone_confidence=confidence,
        rate_toman_per_gram=rate,
        weight_grams=weight,
        legacy_price_toman=legacy,
        calculated_raw_toman=calculated_raw,
        calculated_price_toman=calculated_integer,
        selected_pre_round_toman=selected_integer,
        final_price_toman=final_price,
        selection_reason=reason,
        requires_review=requires_review,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def price_difference_flags(result: PricingResult) -> Tuple[str, ...]:
    if result.legacy_price_toman is None or result.calculated_price_toman is None:
        return tuple()
    legacy = Decimal(result.legacy_price_toman)
    calculated = Decimal(result.calculated_price_toman)
    baseline = max(Decimal(1), min(legacy, calculated))
    difference = abs(legacy - calculated) / baseline
    if difference < Decimal("0.30"):
        return tuple()
    if legacy > calculated:
        return ("source price significantly above calculated floor",)
    return ("source price significantly below calculated floor",)
