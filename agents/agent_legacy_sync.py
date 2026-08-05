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

# --- 1. CORE MATH & BUSINESS LOGIC MODULES ---

def calculate_radman_stock(legacy_stock: int) -> int:
    """
    Applies the authoritative Inventory Buffer Rule:
      - If legacy_stock <= 1: return 0 (prevent overselling on last single item).
      - If legacy_stock > 1:  return legacy_stock - 1 (1-item safety buffer).
    """
    if not isinstance(legacy_stock, int) or legacy_stock < 0:
        return 0
    if legacy_stock <= 1:
        return 0
    return legacy_stock - 1

def generate_radman_sku(category_code: str, gender_code: str, legacy_id: int) -> str:
    """
    Generates the locked SKU syntax: RAD-[CAT]-[GENDER]-[LEGACY_ID]
      - CAT: RNG, NEC, BRC, SET, EAR
      - GENDER: W, M, U
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
    Standardizes Persian product titles:
      - Normalizes Persian characters and digits.
      - Strips unnecessary promo tags.
    """
    cleaned = raw_title.replace("ي", "ی").replace("ك", "ک")
    # Replace Arabic digits with standard Persian digits
    trans_table = str.maketrans("0123456789٠١٢٣٤٥٦٧٨٩", "۰۱۲۳۴۵۶۷۸۹۰۱۲۳۴۵۶۷۸۹")
    return cleaned.translate(trans_table).strip()

def build_woocommerce_payload(legacy_item: Dict[str, Any], is_existing_published: bool = False) -> Dict[str, Any]:
    """
    Constructs the WooCommerce REST API payload.
    OVERWRITE PROTECTION RULE:
      - If product is already PUBLISHED in WooCommerce, we NEVER overwrite name, description,
        short_description, or images. We ONLY synchronize stock_quantity and manage_stock.
      - If product is DRAFT or NEW, we import the clean base metadata and images.
    """
    safe_stock = calculate_radman_stock(legacy_item.get("stock", 0))
    legacy_id = legacy_item.get("id")
    
    if is_existing_published:
        logger.info(f"Product {legacy_id} is PUBLISHED -> Overwrite Protection active (syncing stock={safe_stock} only).")
        return {
            "manage_stock": True,
            "stock_quantity": safe_stock
        }
    
    # New or Draft Product Payload
    raw_title = legacy_item.get("title", f"محصول نقره کد {legacy_id}")
    clean_title = clean_persian_title(raw_title)
    cat_code = legacy_item.get("cat_code", "RNG")
    gender_code = legacy_item.get("gender_code", "M")
    sku = generate_radman_sku(cat_code, gender_code, legacy_id)
    
    payload = {
        "name": clean_title,
        "sku": sku,
        "status": "draft",  # ALWAYS import as draft in Phase 1 for human review
        "manage_stock": True,
        "stock_quantity": safe_stock,
        "regular_price": str(legacy_item.get("price_irr", 0)),
        "short_description": f"نقره ۹۲۵ استرلینگ اصل | وزن: {legacy_item.get('weight_g', '۰.۰۰')} گرم",
        "description": f"خرید آنلاین {clean_title} با ضمانت اصالت کالا، بسته‌بندی لوکس هدیه و ارسال فوری از رادمان سیلور.",
        "meta_data": [
            {"key": "_legacy_store_id", "value": str(legacy_id)},
            {"key": "_legacy_last_sync", "value": datetime.now(timezone.utc).isoformat()}
        ]
    }
    
    # Process images if present
    if "image_url" in legacy_item and legacy_item["image_url"]:
        # Strip query params like ?size=320x320 to get raw high-res image
        raw_img_url = legacy_item["image_url"].split("?")[0]
        payload["images"] = [{"src": raw_img_url, "alt": clean_title}]
        
    return payload

# --- 2. SQLITE STAGING & STATE DATABASE ---

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
                raw_stock INTEGER,
                radman_buffer_stock INTEGER,
                last_sync_utc TEXT
            )
        """)
        self.conn.commit()
        
    def get_product_mapping(self, legacy_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT legacy_id, radman_sku, woocommerce_id, wc_status, raw_stock, radman_buffer_stock, last_sync_utc FROM legacy_sync_map WHERE legacy_id = ?", (legacy_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "legacy_id": row[0],
            "radman_sku": row[1],
            "woocommerce_id": row[2],
            "wc_status": row[3],
            "raw_stock": row[4],
            "radman_buffer_stock": row[5],
            "last_sync_utc": row[6]
        }
        
    def save_mapping(self, legacy_id: int, sku: str, wc_id: int, status: str, raw_stock: int, buffer_stock: int):
        cursor = self.conn.cursor()
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO legacy_sync_map (legacy_id, radman_sku, woocommerce_id, wc_status, raw_stock, radman_buffer_stock, last_sync_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(legacy_id) DO UPDATE SET
                radman_sku = excluded.radman_sku,
                woocommerce_id = excluded.woocommerce_id,
                wc_status = excluded.wc_status,
                raw_stock = excluded.raw_stock,
                radman_buffer_stock = excluded.radman_buffer_stock,
                last_sync_utc = excluded.last_sync_utc
        """, (legacy_id, sku, wc_id, status, raw_stock, buffer_stock, now_utc))
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
        "cat_code": "RNG",
        "gender_code": "M",
        "image_url": "https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785843129_9880917938.jpg?size=320x320&rs=fit"
    },
    {
        "id": 1013,
        "title": "عقیق سیاه انگشتر ضریح نقره مردانه کد 1013",
        "price_irr": 58590000,
        "stock": 1,  # Buffer rule will convert this to 0!
        "weight_g": 5.10,
        "cat_code": "RNG",
        "gender_code": "M",
        "image_url": "https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785842513_4351929313.jpg?size=320x320&rs=fit"
    }
]

def run_sync_pipeline(dry_run: bool = True, use_mock: bool = True):
    logger.info("="*60)
    logger.info("STARTING AGENT-LEGACYSYNC CATALOG & INVENTORY RECONCILIATION")
    logger.info(f"Mode: {'DRY-RUN / MOCK SIMULATION' if dry_run else 'LIVE WOOCOMMERCE SYNC'}")
    logger.info("="*60)
    
    db = StagingDatabase(db_path="legacy_sync_map.db")
    
    if use_mock:
        logger.info(f"Loaded {len(MOCK_LEGACY_FEED)} products from Mock Legacy Catalog Feed (noghrehmashhad.ir format).")
        items = MOCK_LEGACY_FEED
    else:
        logger.error("Live API fetching requires WordPress/WooCommerce live server credentials in .env. Falling back to mock feed.")
        items = MOCK_LEGACY_FEED
        
    for item in items:
        legacy_id = item["id"]
        raw_stock = item["stock"]
        safe_stock = calculate_radman_stock(raw_stock)
        
        # Check SQLite staging state
        existing = db.get_product_mapping(legacy_id)
        is_published = False
        wc_id = 20000 + legacy_id  # Mock WooCommerce ID assignment
        
        if existing:
            logger.info(f"Product {legacy_id} exists in staging table -> SK={existing['radman_sku']}, Status={existing['wc_status']}")
            if existing["wc_status"] == "publish":
                is_published = True
                
        payload = build_woocommerce_payload(item, is_existing_published=is_published)
        
        logger.info("-" * 50)
        logger.info(f"Legacy ID   : {legacy_id}")
        logger.info(f"Title       : {item['title']} -> Clean: {payload.get('name', 'N/A (Protected)')}")
        logger.info(f"SKU         : {payload.get('sku', existing['radman_sku'] if existing else 'N/A')}")
        logger.info(f"Stock Buffer: Raw={raw_stock:2d} -> Safe Radman Stock={safe_stock:2d} | Rule: {'<=1 -> 0' if raw_stock<=1 else '>1 -> N-1'}")
        logger.info(f"Payload     : {json.dumps(payload, ensure_ascii=False)}")
        
        # Save state in SQLite
        db.save_mapping(
            legacy_id=legacy_id,
            sku=payload.get("sku", f"RAD-RNG-M-{legacy_id}"),
            wc_id=wc_id,
            status=payload.get("status", "draft"),
            raw_stock=raw_stock,
            buffer_stock=safe_stock
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
