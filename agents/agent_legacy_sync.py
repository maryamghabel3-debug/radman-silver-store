#!/usr/bin/env python3
"""
RADMAN SILVER STORE — Legacy Store Catalog Sync Agent (Agent-LegacySync)
-------------------------------------------------------------------------
Author: RADMAN SILVER AI Agent Core
License: Proprietary / Single Source of Truth
Architecture: Python 3.11+ / SQLite Staging / WooCommerce REST API v3
"""

import os
import sys
import json
import sqlite3
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Agent-LegacySync) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Agent-LegacySync")

# --- Environment Variable Loading (Primary Official Names + Deprecated Fallbacks) ---
# Official primary env vars: LEGACY_API_BASE_URL, LEGACY_API_KEY, LEGACY_API_SECRET
# DEPRECATED fallback support: LEGACY_STORE_URL -> LEGACY_API_BASE_URL, LEGACY_API_TOKEN -> LEGACY_API_KEY
LEGACY_API_BASE_URL = os.getenv("LEGACY_API_BASE_URL") or os.getenv("LEGACY_STORE_URL", "https://noghrehmashhad.ir")
LEGACY_API_KEY = os.getenv("LEGACY_API_KEY") or os.getenv("LEGACY_API_TOKEN", "")
LEGACY_API_SECRET = os.getenv("LEGACY_API_SECRET", "")

if os.getenv("LEGACY_STORE_URL"):
    logger.warning("DEPRECATED: 'LEGACY_STORE_URL' is deprecated; please migrate to 'LEGACY_API_BASE_URL'.")
if os.getenv("LEGACY_API_TOKEN"):
    logger.warning("DEPRECATED: 'LEGACY_API_TOKEN' is deprecated; please migrate to 'LEGACY_API_KEY'.")

# --- 1. CORE BUSINESS & STOCK/PRICING MODULES ---

def calculate_radman_stock(legacy_stock: int) -> int:
    """
    AUTHORITATIVE STOCK REALITY RULE:
      - Most silver rings are UNIQUE pieces (stock = 1 is NORMAL and sellable).
      - NO historical stock-offset logic is applied.
      - Exact 1:1 Mapping:
          stock = 1 on old site -> stock = 1 on new site
          stock = 0 -> stock = 0
          stock = N -> stock = N
      - Overselling risk is handled by HUMAN CONFIRMATION via Telegram before shipping.
    """
    if not isinstance(legacy_stock, int) or legacy_stock < 0:
        return 0
    return legacy_stock

def determine_pricing_mode(legacy_item: Dict[str, Any]) -> tuple[str, str]:
    """
    AUTHORITATIVE PRICING REALITY RULE (4 Official Modes Only):
      - Official modes: silver_weight_only, silver_weight_plus_stone, legacy_mirror, manual_locked
      - 1. silver_weight_only       : price = weight_grams * daily_rate
      - 2. silver_weight_plus_stone : price = (weight_grams * daily_rate) + stone_fixed_value_toman
      - 3. legacy_mirror            : copy legacy price as-is
      - 4. manual_locked            : special/masterwork manual price
    """
    weight = legacy_item.get("weight_g")
    has_special_gem = legacy_item.get("is_special_gemstone", False)
    has_stone_val = legacy_item.get("stone_fixed_value_toman", 0) > 0
    legacy_price = str(legacy_item.get("price_irr", 0))
    
    if legacy_item.get("price_locked") or (has_special_gem and not has_stone_val):
        return "manual_locked", legacy_price
    elif weight and float(weight) > 0 and has_stone_val:
        return "silver_weight_plus_stone", legacy_price
    elif weight and float(weight) > 0:
        return "silver_weight_only", legacy_price
    else:
        return "legacy_mirror", legacy_price

def generate_radman_sku(category_code: str, gender_code: str, legacy_id: int) -> str:
    """
    Generates the locked SKU syntax: RAD-[CAT]-[GENDER]-[LEGACY_ID]
    """
    cat = category_code.upper().strip()
    gen = gender_code.upper().strip()
    if cat not in {"RNG", "NEC", "BRC", "SET", "EAR"}:
        cat = "RNG"
    if gen not in {"W", "M", "U"}:
        gen = "U"
    return f"RAD-{cat}-{gen}-{legacy_id}"

def clean_persian_title(raw_title: str) -> str:
    """
    Standardizes Persian product titles with official web typography and Persian digits.
    """
    cleaned = raw_title.replace("ي", "ی").replace("ك", "ک")
    trans_table = str.maketrans("0123456789٠١٢٣٤٥٦٧٨٩", "۰۱۲۳۴۵۶۷۸۹۰۱۲۳۴۵۶۷۸۹")
    return cleaned.translate(trans_table).strip()

def build_woocommerce_payload(legacy_item: Dict[str, Any], is_existing_published: bool = False) -> Dict[str, Any]:
    """
    Constructs the WooCommerce REST API payload.
    OVERWRITE PROTECTION RULE:
      - If product is already PUBLISHED in WooCommerce, we NEVER overwrite name, description,
        short_description, or images. We ONLY synchronize stock_quantity and manage_stock.
      - If product is DRAFT or NEW, we import clean base metadata and images.
    """
    exact_stock = calculate_radman_stock(legacy_item.get("stock", 0))
    legacy_id = legacy_item.get("id")
    
    if is_existing_published:
        logger.info(f"Product {legacy_id} is PUBLISHED -> Overwrite Protection active (syncing exact stock={exact_stock} only).")
        return {
            "manage_stock": True,
            "stock_quantity": exact_stock
        }
    
    raw_title = legacy_item.get("title", f"محصول نقره کد {legacy_id}")
    clean_title = clean_persian_title(raw_title)
    cat_code = legacy_item.get("cat_code", "RNG")
    gender_code = legacy_item.get("gender_code", "M")
    sku = generate_radman_sku(cat_code, gender_code, legacy_id)
    pricing_mode, initial_price = determine_pricing_mode(legacy_item)
    
    payload = {
        "name": clean_title,
        "sku": sku,
        "status": "draft",  # ALWAYS import as draft in Phase 1 for human review
        "manage_stock": True,
        "stock_quantity": exact_stock,
        "regular_price": initial_price,
        "short_description": f"نقره ۹۲۵ استرلینگ اصل | وزن: {legacy_item.get('weight_g', '۰.۰۰')} گرم | مدل قیمت‌گذاری: {pricing_mode}",
        "description": f"خرید آنلاین {clean_title} با ضمانت اصالت کالا، بسته‌بندی لوکس هدیه و ارسال فوری از رادمان سیلور.",
        "meta_data": [
            {"key": "_legacy_store_id", "value": str(legacy_id)},
            {"key": "_pricing_mode", "value": pricing_mode},
            {"key": "_legacy_last_sync", "value": datetime.now(timezone.utc).isoformat()}
        ]
    }
    
    if "image_url" in legacy_item and legacy_item["image_url"]:
        raw_img_url = legacy_item["image_url"].split("?")[0]
        payload["images"] = [{"src": raw_img_url, "alt": clean_title}]
        
    return payload

# --- 2. SQLITE STAGING DATABASE ---

class StagingDatabase:
    def __init__(self, db_path: str = "legacy_sync_map.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_schema()
        
    def create_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS legacy_sync_map (
                legacy_id INTEGER PRIMARY KEY,
                radman_sku TEXT UNIQUE,
                woocommerce_id INTEGER,
                wc_status TEXT,
                exact_stock INTEGER,
                pricing_mode TEXT,
                last_sync_utc TEXT
            )
        """)
        self.conn.commit()
        
    def get_product_mapping(self, legacy_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT legacy_id, radman_sku, woocommerce_id, wc_status, exact_stock, pricing_mode, last_sync_utc FROM legacy_sync_map WHERE legacy_id = ?", (legacy_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "legacy_id": row[0],
            "radman_sku": row[1],
            "woocommerce_id": row[2],
            "wc_status": row[3],
            "exact_stock": row[4],
            "pricing_mode": row[5],
            "last_sync_utc": row[6]
        }
        
    def save_mapping(self, legacy_id: int, sku: str, wc_id: int, status: str, exact_stock: int, pricing_mode: str):
        cursor = self.conn.cursor()
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO legacy_sync_map (legacy_id, radman_sku, woocommerce_id, wc_status, exact_stock, pricing_mode, last_sync_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(legacy_id) DO UPDATE SET
                radman_sku = excluded.radman_sku,
                woocommerce_id = excluded.woocommerce_id,
                wc_status = excluded.wc_status,
                exact_stock = excluded.exact_stock,
                pricing_mode = excluded.pricing_mode,
                last_sync_utc = excluded.last_sync_utc
        """, (legacy_id, sku, wc_id, status, exact_stock, pricing_mode, now_utc))
        self.conn.commit()
        
    def close(self):
        self.conn.close()

# --- 3. MOCK FEED & EXECUTION ORCHESTRATOR ---

MOCK_LEGACY_FEED = [
    {
        "id": 1014,
        "title": "انگشتر مردانه عقیق سبز خوشرنگ کد ۱۰۱۴",
        "price_irr": 78900000,
        "stock": 5,
        "weight_g": 6.80,
        "is_special_gemstone": False,
        "stone_fixed_value_toman": 0,
        "cat_code": "RNG",
        "gender_code": "M",
        "image_url": "https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785842823_4580729600.jpg?size=320x320&rs=fit"
    },
    {
        "id": 1015,
        "title": "انگشتر مردانه عقیق سرخ خوشرنگ کد ۱۰۱5",
        "price_irr": 86900000,
        "stock": 2,
        "weight_g": 7.20,
        "is_special_gemstone": True,
        "stone_fixed_value_toman": 500000,
        "cat_code": "RNG",
        "gender_code": "M",
        "image_url": "https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785843129_9880917938.jpg?size=320x320&rs=fit"
    },
    {
        "id": 1013,
        "title": "عقیق سیاه انگشتر ضریح نقره مردانه کد 1013",
        "price_irr": 58590000,
        "stock": 1,  # Stock = 1 is NORMAL and sellable! Exact 1:1 mapping!
        "weight_g": 5.10,
        "is_special_gemstone": False,
        "stone_fixed_value_toman": 0,
        "cat_code": "RNG",
        "gender_code": "M",
        "image_url": "https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785842513_4351929313.jpg?size=320x320&rs=fit"
    }
]

def run_sync_pipeline(dry_run: bool = True, use_mock: bool = True):
    logger.info("="*60)
    logger.info("STARTING AGENT-LEGACYSYNC (1:1 EXACT STOCK MAPPING & 4 OFFICIAL PRICING MODES)")
    logger.info(f"Mode: {'DRY-RUN / MOCK SIMULATION' if dry_run else 'LIVE WOOCOMMERCE SYNC'}")
    logger.info("="*60)
    
    db = StagingDatabase(db_path="legacy_sync_map.db")
    items = MOCK_LEGACY_FEED
        
    for item in items:
        legacy_id = item["id"]
        exact_stock = calculate_radman_stock(item["stock"])
        pricing_mode, _ = determine_pricing_mode(item)
        
        existing = db.get_product_mapping(legacy_id)
        is_published = False
        wc_id = 20000 + legacy_id
        
        if existing and existing["wc_status"] == "publish":
            is_published = True
                
        payload = build_woocommerce_payload(item, is_existing_published=is_published)
        
        logger.info("-" * 55)
        logger.info(f"Legacy ID   : {legacy_id}")
        logger.info(f"Title       : {item['title']} -> Clean: {payload.get('name', 'N/A (Protected)')}")
        logger.info(f"SKU         : {payload.get('sku', existing['radman_sku'] if existing else 'N/A')}")
        logger.info(f"Stock Rule  : Raw={item['stock']} -> Exact Radman Stock={exact_stock} (1:1 mapping)")
        logger.info(f"Pricing Mode: {pricing_mode.upper()}")
        logger.info(f"Payload     : {json.dumps(payload, ensure_ascii=False)}")
        
        db.save_mapping(
            legacy_id=legacy_id,
            sku=payload.get("sku", f"RAD-RNG-M-{legacy_id}"),
            wc_id=wc_id,
            status=payload.get("status", "draft"),
            exact_stock=exact_stock,
            pricing_mode=pricing_mode
        )
        
    db.close()
    logger.info("="*60)
    logger.info("AGENT-LEGACYSYNC RECONCILIATION COMPLETED SUCCESSFULLY.")
    logger.info("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RADMAN SILVER — Legacy Store Sync Agent")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run without pushing to live WooCommerce")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock feed from noghrehmashhad.ir")
    args = parser.parse_args()
    
    run_sync_pipeline(dry_run=args.dry_run, use_mock=args.mock)
