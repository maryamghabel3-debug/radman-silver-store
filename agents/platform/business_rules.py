"""
Business Rules & Data Source Verification Engine
=================================================
Validates catalog items, pricing, inventory settings, content descriptions,
and factual provenance against RADMAN SILVER 925 verified business rules.

Authoritative Data-Source Rules (2026-09-03):
1. Weight comes ONLY from WooCommerce meta _weight (or snapshot). Never infer or derive from price.
2. Price comes ONLY from WooCommerce _regular_price. Never compute, round, or alter in SEO/GEO/AEO.
3. PRICE_IN_META_DESCRIPTION = FORBIDDEN: Fixed prices in <meta description> go stale and are rejected.
4. Adjectives like 'طبیعی' or stone specifics are ONLY allowed if present in the verified stone field.
5. Every factual claim must have verified provenance {value, source_field, verified=True}.
6. Forbidden unless verified: دست‌ساز, شناسنامه, اصالت‌نامه, بسته‌بندی, گارانتی, ضمانت, آبدار, سه پوست, نرخ مصوب, نرخ روز, عرضه مستقیم.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PricingValidationResult:
    is_valid: bool
    calculated_floor_toman: int
    proposed_price_toman: int
    gram_rate_applied: int
    violations: List[str] = field(default_factory=list)
    variance_ratio: float = 0.0
    requires_gate: Optional[str] = None


@dataclass
class ContentValidationResult:
    is_valid: bool
    violations: List[str] = field(default_factory=list)
    detected_patterns: List[str] = field(default_factory=list)
    clean_text: str = ""


@dataclass
class ProductValidationResult:
    is_valid: bool
    verdict: str  # PASS, WARN, BLOCKED
    passed_checks: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    required_gates: List[str] = field(default_factory=list)


class RadmanBusinessRules:
    """Core business rule & provenance validator for RADMAN SILVER 925."""

    DEFAULT_RULES_PATH = Path(".agents/config/radman-business-rules.json")
    DEFAULT_SNAPSHOT_PATH = Path("data/verified-product-snapshot-20260903.json")

    STANDARD_GRAM_RATE = 650_000
    LARGE_STONE_GRAM_RATE = 590_000
    PRICE_VARIANCE_GATE_THRESHOLD = 0.05  # 5%
    PRICE_IN_META_DESCRIPTION = "FORBIDDEN"

    PHONE_PATTERNS = [
        re.compile(r"09\d{9}"),
        re.compile(r"\+98\d{10}"),
        re.compile(r"۰۹[۰-۹]{9}"),
    ]

    SHIPPING_PROMISE_KEYWORDS = [
        "ارسال فوری تضمینی",
        "تحویل ۲۴ ساعته",
        "ارسال همان روز",
        "ارسال ۱ ساعته",
        "تحویل فوری قطعی",
    ]

    GUARANTEE_CLAIM_KEYWORDS = [
        "گارانتی مادام‌العمر",
        "ضمانت همیشگی",
        "تضمین ۱۰۰٪ بدون تغییر رنگ",
        "غیر قابل شکستن",
        "ضمانت بی‌قید و شرط",
        "ضمانت اصالت",
    ]

    FORBIDDEN_UNVERIFIED_CLAIMS = [
        "دست‌ساز",
        "دست ساز",
        "شناسنامه",
        "اصالت‌نامه",
        "اصالت نامه",
        "بسته‌بندی",
        "بسته بندی",
        "گارانتی",
        "ضمانت",
        "آبدار",
        "سه پوست",
        "نرخ مصوب",
        "نرخ روز",
        "عرضه مستقیم",
    ]

    PRICE_IN_META_PATTERNS = [
        re.compile(r"\d+([,،]\d+)*\s*(تومان|ریال|IRT|IRR)", re.I),
        re.compile(r"قیمت", re.I),
    ]

    def __init__(self, config_path: Optional[Path] = None, snapshot_path: Optional[Path] = None) -> None:
        self.config_path = config_path or self._resolve_path(self.DEFAULT_RULES_PATH)
        self.snapshot_path = snapshot_path or self._resolve_path(self.DEFAULT_SNAPSHOT_PATH)
        self.rules_data: Dict[str, Any] = {}
        self.snapshot_data: Dict[str, Any] = {}
        self.load()

    def _resolve_path(self, default_rel: Path) -> Path:
        cwd = Path.cwd()
        candidate = cwd / default_rel
        if candidate.exists():
            return candidate

        repo_root = Path(__file__).resolve().parent.parent.parent
        candidate = repo_root / default_rel
        if candidate.exists():
            return candidate

        return Path(default_rel)

    def load(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.rules_data = json.load(f)
        if self.snapshot_path.exists():
            with open(self.snapshot_path, "r", encoding="utf-8") as f:
                self.snapshot_data = json.load(f)

    @classmethod
    def get_gram_rate(cls, stone_type: str = "standard") -> int:
        st_lower = stone_type.strip().lower()
        if st_lower in ("large_stone", "large", "confirmed_large_stone", "درشت", "سنگ درشت"):
            return cls.LARGE_STONE_GRAM_RATE
        return cls.STANDARD_GRAM_RATE

    @classmethod
    def calculate_price_floor(
        cls,
        weight_grams: float,
        stone_type: str = "standard",
        legacy_price: Optional[int] = None,
    ) -> int:
        """Calculates exact price floor: max(legacy_price, weight * gram_rate)."""
        rate = cls.get_gram_rate(stone_type)
        weight_dec = Decimal(str(weight_grams))
        floor_dec = weight_dec * Decimal(str(rate))
        computed_floor = int(math.ceil(float(floor_dec)))

        if legacy_price is not None and legacy_price > 0:
            return max(int(legacy_price), computed_floor)
        return computed_floor

    @classmethod
    def validate_pricing(
        cls,
        proposed_price_toman: int,
        weight_grams: float,
        stone_type: str = "standard",
        legacy_price: Optional[int] = None,
        baseline_price: Optional[int] = None,
        sale_price: Optional[Any] = None,
    ) -> PricingValidationResult:
        """Validates pricing proposal against RADMAN pricing rules."""
        violations: List[str] = []
        requires_gate: Optional[str] = None

        # Rule 1: Sale price is strictly forbidden
        if sale_price is not None and str(sale_price).strip() not in ("", "None", "0"):
            violations.append("BR-PRC-01: sale_price or strikethrough price is strictly forbidden in RADMAN luxury policy.")

        rate = cls.get_gram_rate(stone_type)
        floor = cls.calculate_price_floor(weight_grams, stone_type, legacy_price)

        # Rule 2: Proposed price cannot be below calculated floor
        if proposed_price_toman < floor:
            violations.append(
                f"BR-PRC-02: Proposed price ({proposed_price_toman:,} Toman) is below minimum price floor ({floor:,} Toman)."
            )

        # Rule 3: Check variance ratio for approval gate (> 5%)
        variance_ratio = 0.0
        if baseline_price and baseline_price > 0:
            variance_ratio = abs(proposed_price_toman - baseline_price) / float(baseline_price)
            if variance_ratio > cls.PRICE_VARIANCE_GATE_THRESHOLD:
                requires_gate = "GATE_PRICE_CHANGE_LARGE"

        is_valid = len(violations) == 0
        return PricingValidationResult(
            is_valid=is_valid,
            calculated_floor_toman=floor,
            proposed_price_toman=proposed_price_toman,
            gram_rate_applied=rate,
            violations=violations,
            variance_ratio=variance_ratio,
            requires_gate=requires_gate,
        )

    @classmethod
    def validate_data_source_price(cls, proposed_price: int, verified_regular_price: int) -> bool:
        """Rule 2: Price must match verified WooCommerce _regular_price exactly."""
        return proposed_price == verified_regular_price

    @classmethod
    def validate_meta_description_no_price(cls, meta_text: str) -> ContentValidationResult:
        """Rule 3: Price in meta description is strictly forbidden (goes stale in Google)."""
        violations: List[str] = []
        detected: List[str] = []

        for pat in cls.PRICE_IN_META_PATTERNS:
            matches = pat.findall(meta_text)
            if matches:
                violations.append("BR-META-01: Price detected in meta description. Prices in meta descriptions go stale and are strictly forbidden.")
                detected.extend([str(m) for m in matches])

        if "تومان" in meta_text or "ریال" in meta_text:
            violations.append("BR-META-02: Currency token (تومان/ریال) detected in meta description.")
            detected.append("currency_token")

        is_valid = len(violations) == 0
        return ContentValidationResult(
            is_valid=is_valid,
            violations=violations,
            detected_patterns=detected,
            clean_text=meta_text,
        )

    @classmethod
    def validate_content(cls, text: str, is_meta_description: bool = False) -> ContentValidationResult:
        """Audits public description or copy for prohibited claims, phone numbers, and unverified words."""
        violations: List[str] = []
        detected_patterns: List[str] = []

        if not text:
            return ContentValidationResult(is_valid=True, clean_text="")

        # Check price in meta description
        if is_meta_description:
            price_meta_res = cls.validate_meta_description_no_price(text)
            if not price_meta_res.is_valid:
                violations.extend(price_meta_res.violations)
                detected_patterns.extend(price_meta_res.detected_patterns)

        # Check phone numbers
        for pat in cls.PHONE_PATTERNS:
            matches = pat.findall(text)
            if matches:
                violations.append("BR-CNT-01: Direct telephone or mobile numbers are prohibited in public descriptions.")
                detected_patterns.extend(matches)

        # Check shipping promises
        for kw in cls.SHIPPING_PROMISE_KEYWORDS:
            if kw in text:
                violations.append(f"BR-CNT-02: Prohibited shipping guarantee claim detected: '{kw}'.")
                detected_patterns.append(kw)

        # Check warranty promises
        for kw in cls.GUARANTEE_CLAIM_KEYWORDS:
            if kw in text:
                violations.append(f"BR-CNT-03: Prohibited absolute warranty claim detected: '{kw}'.")
                detected_patterns.append(kw)

        # Check unverified claims
        for uw in cls.FORBIDDEN_UNVERIFIED_CLAIMS:
            if uw in text:
                violations.append(f"BR-FACT-01: Prohibited unverified factual claim detected: '{uw}'.")
                detected_patterns.append(uw)

        is_valid = len(violations) == 0
        return ContentValidationResult(
            is_valid=is_valid,
            violations=violations,
            detected_patterns=detected_patterns,
            clean_text=text,
        )

    @classmethod
    def validate_weight_rule(cls, text: str, verified_weight_g: Optional[int]) -> bool:
        """Rule 1: Weight must come from verified field or be omitted entirely."""
        if not verified_weight_g:
            if re.search(r"\d+(\.\d+)?\s*(گرم|g|gram)", text, re.I):
                return False
        return True

    @classmethod
    def validate_product_payload(
        cls,
        payload: Dict[str, Any],
        baseline_price: Optional[int] = None,
    ) -> ProductValidationResult:
        """Full preflight audit of a product payload."""
        passed_checks: List[str] = []
        violations: List[str] = []
        blockers: List[str] = []
        required_gates: List[str] = []

        # 1. Check sale price
        sale_price = payload.get("sale_price")
        if sale_price is not None and str(sale_price).strip() not in ("", "None", "0"):
            violations.append("BR-PRC-01: sale_price cannot be set.")
            blockers.append("SALE_PRICE_NOT_ALLOWED")
        else:
            passed_checks.append("CHECK_NO_SALE_PRICE")

        # 2. Check stock model (1:1)
        stock_qty = payload.get("stock_quantity")
        if stock_qty is not None and int(stock_qty) != 1:
            violations.append(f"BR-STK-01: Stock quantity must be 1 for unique luxury pieces, got {stock_qty}.")
            blockers.append("STOCK_MODEL_VIOLATION")
        else:
            passed_checks.append("CHECK_STOCK_1TO1")

        # 3. Check draft status preservation
        status = payload.get("status", "draft")
        if status != "draft":
            violations.append(f"BR-LFC-01: Automated status must be 'draft', cannot set '{status}' directly.")
            required_gates.append("GATE_PUBLISH_PRODUCT")
        else:
            passed_checks.append("CHECK_DRAFT_STATUS")

        # 4. Check price floor
        weight = float(payload.get("weight_grams", payload.get("weight", payload.get("weight_g", 0.0))))
        proposed_price = int(payload.get("price", payload.get("regular_price", payload.get("regular_price_IRT", 0))))
        stone_type = payload.get("stone_type", "standard")
        legacy_price = payload.get("legacy_price")

        if weight > 0 and proposed_price > 0:
            pricing_res = cls.validate_pricing(
                proposed_price_toman=proposed_price,
                weight_grams=weight,
                stone_type=stone_type,
                legacy_price=legacy_price,
                baseline_price=baseline_price,
                sale_price=sale_price,
            )
            if not pricing_res.is_valid:
                violations.extend(pricing_res.violations)
                blockers.append("PRICE_BELOW_FLOOR")
            else:
                passed_checks.append("CHECK_PRICE_FLOOR")

            if pricing_res.requires_gate:
                required_gates.append(pricing_res.requires_gate)
        else:
            passed_checks.append("CHECK_PRICE_SKIPPED_MISSING_WEIGHT")

        # 5. Check description content safety
        description = payload.get("description", "")
        if description:
            content_res = cls.validate_content(description)
            if not content_res.is_valid:
                violations.extend(content_res.violations)
                blockers.append("PROHIBITED_CONTENT_DETECTED")
            else:
                passed_checks.append("CHECK_CONTENT_PURITY")
        else:
            passed_checks.append("CHECK_CONTENT_EMPTY")

        # Determine verdict
        if blockers:
            verdict = "BLOCKED"
        elif required_gates:
            verdict = "REQUIRES_APPROVAL"
        else:
            verdict = "PASS"

        is_valid = len(blockers) == 0
        return ProductValidationResult(
            is_valid=is_valid,
            verdict=verdict,
            passed_checks=passed_checks,
            violations=violations,
            blockers=blockers,
            required_gates=required_gates,
        )
