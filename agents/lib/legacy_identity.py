"""Deterministic legacy product-code extraction and WooCommerce SKU mapping."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
SAFE_SKU_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


@dataclass(frozen=True)
class LegacyIdentity:
    legacy_code_raw: Optional[str]
    legacy_code: Optional[str]
    sku: Optional[str]
    normalization_required: bool
    mapping_reason: str
    requires_review: bool


def normalize_digits(value: str) -> str:
    return str(value or "").translate(_DIGITS).replace("ي", "ی").replace("ك", "ک")


def _clean_code_token(value: str) -> str:
    return normalize_digits(value).strip().strip(".:：،,؛;#()[]{}")


def extract_legacy_code(title: str, visible_text: str) -> Optional[str]:
    """Extract the visible code without inventing one.

    Explicit ``شناسه کالا`` wins over title/description ``کد`` markers.
    """
    sources: Sequence[tuple[str, str]] = (
        ("explicit", visible_text or ""),
        ("title", title or ""),
        ("fallback", visible_text or ""),
    )
    patterns = {
        "explicit": (
            r"شناسه\s*کالا\s*[:：#-]?\s*([A-Za-z0-9۰-۹٠-٩._/-]{1,100})",
        ),
        "title": (
            r"(?:کد|كد|code)\s*[:：#-]?\s*([A-Za-z0-9۰-۹٠-٩._/-]{1,100})",
        ),
        "fallback": (
            r"(?:کد|كد|code)\s*[:：#-]?\s*([A-Za-z0-9۰-۹٠-٩._/-]{1,100})",
        ),
    }
    for source_name, source in sources:
        # Match the rendered token before digit normalization so valid ASCII codes
        # remain byte-for-byte SKUs and localized codes remain available as raw metadata.
        rendered_source = str(source or "").replace("ي", "ی").replace("ك", "ک")
        for pattern in patterns[source_name]:
            match = re.search(pattern, rendered_source, flags=re.IGNORECASE)
            if match:
                token = str(match.group(1)).strip().strip(".:：،,؛;#()[]{}")
                if token:
                    return token
    return None


def map_legacy_code_to_sku(code: Optional[str]) -> LegacyIdentity:
    if code is None or not str(code).strip():
        return LegacyIdentity(
            legacy_code_raw=None,
            legacy_code=None,
            sku=None,
            normalization_required=False,
            mapping_reason="MISSING_CODE",
            requires_review=True,
        )

    raw = str(code).strip()
    normalized = _clean_code_token(raw)
    if SAFE_SKU_RE.fullmatch(raw):
        return LegacyIdentity(
            legacy_code_raw=raw,
            legacy_code=normalized,
            sku=raw,
            normalization_required=False,
            mapping_reason="EXACT_LEGACY_CODE",
            requires_review=False,
        )
    if SAFE_SKU_RE.fullmatch(normalized):
        return LegacyIdentity(
            legacy_code_raw=raw,
            legacy_code=normalized,
            sku=normalized,
            normalization_required=True,
            mapping_reason="DIGIT_OR_CHARACTER_NORMALIZATION",
            requires_review=False,
        )

    ascii_base = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip("-._")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()
    if ascii_base:
        ascii_base = ascii_base[:70]
        sku = f"LEGACY-{ascii_base}-{digest}"
    else:
        sku = f"LEGACY-{digest}"
    return LegacyIdentity(
        legacy_code_raw=raw,
        legacy_code=normalized or raw,
        sku=sku,
        normalization_required=True,
        mapping_reason="DETERMINISTIC_SAFE_SKU",
        requires_review=False,
    )


def duplicate_codes(identities: Iterable[LegacyIdentity]) -> Set[str]:
    groups: Dict[str, List[LegacyIdentity]] = {}
    for identity in identities:
        if not identity.legacy_code:
            continue
        key = normalize_digits(identity.legacy_code).casefold()
        groups.setdefault(key, []).append(identity)
    return {key for key, values in groups.items() if len(values) > 1}
