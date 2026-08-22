#!/usr/bin/env python3
"""Offline fixture tests for PR-28A Excel catalog analysis."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "excel-catalog" / "small_catalog_rows.json"
sys.path.insert(0, str(SCRIPTS_DIR))

import analyze_excel_catalog as analyzer  # noqa: E402


def make_xlsx(path: Path) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = analyzer.SHEET_NAME
    sheet.append(fixture["headers"])
    for product in fixture["products"]:
        row = [None] * 29
        row[analyzer.COL_ID - 1] = product["id"]
        row[analyzer.COL_TITLE - 1] = product["title"]
        row[analyzer.COL_CATEGORY - 1] = product["category"]
        row[analyzer.COL_PRICE - 1] = product["price"]
        row[analyzer.COL_AVAILABILITY - 1] = product["availability"]
        row[analyzer.COL_ACTIVE - 1] = product["active"]
        row[analyzer.COL_WEIGHT - 1] = product["weight"]
        sheet.append(row)
    workbook.save(path)
    workbook.close()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_category_counting_and_catalog_stats() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        xlsx = Path(temporary) / "small.xlsx"
        make_xlsx(xlsx)
        before = sha256(xlsx)
        rows, headers, warnings = analyzer.load_catalog(xlsx)
        assert analyzer.resolve_title_column(headers) == 2
        analysis = analyzer.analyze_catalog(
            rows,
            headers=headers,
            warnings=warnings,
            expected_rows=8,
            expected_category_count=3,
        )

        assert sha256(xlsx) == before
        assert analysis["total_rows"] == 8
        assert analysis["column_count"] == 29
        assert analysis["category_count"] == 3
        assert analysis["missing_category"] == 1
        assert analysis["category_distribution"] == [
            {"category": "انگشتر عقیق مردانه", "count": 3},
            {"category": "دستبند حدید مردانه", "count": 2},
            {"category": "گردنبند فیروزه زنانه", "count": 2},
        ]
        assert analysis["id_min"] == 1
        assert analysis["id_max"] == 3643
        assert [row["legacy_id"] for row in analysis["lowest_id_products"]] == [
            1,
            2,
            3,
            4,
            3000,
        ]
        assert [row["legacy_id"] for row in analysis["highest_id_products"]] == [
            3643,
            3642,
            3001,
            3000,
            4,
        ]
        assert analysis["weight"]["present"] == 5
        assert analysis["weight"]["missing"] == 3
        assert analysis["weight"]["valid_numeric"] == 4
        assert analysis["weight"]["present_but_invalid"] == 1
        assert analysis["weight"]["coverage_percent"] == Decimal("62.5")
        assert analysis["price"]["count"] == 7
        assert analysis["price"]["minimum"] == Decimal("100000")
        assert analysis["price"]["maximum"] == Decimal("900000")
        assert analysis["active"] == {"active": 5, "inactive": 3, "unknown": 0}
        assert analysis["availability"]["موجود"] == 5
        assert analysis["availability"]["ناموجود"] == 3

        ring_mapping = next(
            item
            for item in analysis["taxonomy_mappings"]
            if item["legacy_category"] == "انگشتر عقیق مردانه"
        )
        assert ring_mapping["parent"] == "انگشتر"
        assert ring_mapping["child"] == "مردانه"
        assert "عقیق" in ring_mapping["facets"]

        report = analyzer.render_report(
            analysis, source_path=xlsx, sheet_name=analyzer.SHEET_NAME
        )
        assert "تعداد دسته یکتای غیرخالی: **3**" in report
        assert "**فرض اعلام‌شده مالک:** ID پایین‌تر یعنی محصول جدیدتر" in report
        assert "| 1 | انگشتر عقیق مردانه | 3 |" in report
        assert "| 1 | انگشتر جدید یک | 100,000 | 5.500 |" in report
        assert "| 3643 | محصول بدون دسته | 900,000 | — |" in report
        assert "سطح ۱" in report and "attribute/tag پیشنهادی" in report
    print("PASS: small XLSX fixture category, ID, weight, price, stock, and taxonomy stats")


def test_cli_outputs_and_source_protection() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        xlsx = root / "small.xlsx"
        text_output = root / "report.txt"
        json_output = root / "report.json"
        make_xlsx(xlsx)
        before = sha256(xlsx)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "analyze_excel_catalog.py"),
                "--excel",
                str(xlsx),
                "--expected-rows",
                "8",
                "--expected-categories",
                "3",
                "--output",
                str(text_output),
                "--json-output",
                str(json_output),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert sha256(xlsx) == before
        assert result.stdout.startswith("# تحلیل کاتالوگ Excel")
        assert text_output.is_file() and json_output.is_file()
        payload = json.loads(json_output.read_text(encoding="utf-8"))
        assert payload["category_count"] == 3
        assert payload["weight"]["coverage_percent"] == "62.5"

        blocked = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "analyze_excel_catalog.py"),
                "--excel",
                str(xlsx),
                "--output",
                str(xlsx),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert blocked.returncode != 0
        assert sha256(xlsx) == before
    print("PASS: CLI text/JSON outputs are atomic and cannot overwrite the source XLSX")


def test_runner_and_no_mutation_contract() -> None:
    runner = SCRIPTS_DIR / "run_catalog_analysis.sh"
    analyzer_source = (SCRIPTS_DIR / "analyze_excel_catalog.py").read_text(
        encoding="utf-8"
    )
    runner_source = runner.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(runner)], check=True)
    assert "subprocess" not in analyzer_source
    assert "urllib" not in analyzer_source
    assert "requests" not in analyzer_source
    assert not re.search(r"(^|\s)wp(\s|$)", runner_source, flags=re.MULTILINE)
    assert "media import" not in runner_source.lower()
    assert "public_html" in runner_source

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        xlsx = root / "small.xlsx"
        private = root / "private"
        make_xlsx(xlsx)
        before = sha256(xlsx)
        result = subprocess.run(
            [
                "bash",
                str(runner),
                "--excel",
                str(xlsx),
                "--private-dir",
                str(private),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        reports = list((private / "legacy-cache").glob("catalog-analysis-*.txt"))
        assert len(reports) == 1
        assert sha256(xlsx) == before
        assert "[SAVED]" in result.stdout
        assert "No WordPress" not in result.stderr
        assert "ID پایین‌تر یعنی محصول جدیدتر" in reports[0].read_text(
            encoding="utf-8"
        )
        created = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path != xlsx
        )
        assert created == [
            "private/legacy-cache/" + reports[0].name,
        ]
    print("PASS: runner writes only one private report and performs no host/WP/media action")


def main() -> int:
    test_category_counting_and_catalog_stats()
    test_cli_outputs_and_source_protection()
    test_runner_and_no_mutation_contract()
    print("ALL EXCEL CATALOG ANALYSIS TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
