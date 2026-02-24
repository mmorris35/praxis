#!/usr/bin/env python3
"""Download all public mortgage underwriting guideline documents."""

import os
import sys
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "pdfs"

SOURCES = [
    {
        "name": "FHA_Handbook_4000.1",
        "url": "https://www.hud.gov/sites/dfiles/OCHCO/documents/4000.1hsgh.pdf",
        "description": "FHA Single Family Housing Policy Handbook",
    },
    {
        "name": "VA_Lenders_Handbook_26-7",
        "url": "https://www.benefits.va.gov/warms/docs/admin26/m26-07/lender_handbook_va_pamphlet_complete.pdf",
        "description": "VA Lender's Handbook (Complete)",
    },
    {
        "name": "VA_Chapter4_Credit_Underwriting",
        "url": "https://benefits.va.gov/warms/docs/admin26/m26-07/chapter_4_credit_underwriting.pdf",
        "description": "VA Chapter 4: Credit Underwriting (standalone)",
    },
    {
        "name": "USDA_HB-1-3555_Guaranteed_Loan",
        "url": "https://www.rd.usda.gov/media/file/download/hb-1-3555-consolidated.pdf",
        "description": "USDA Rural Development Guaranteed Loan Program Handbook",
    },
    {
        "name": "Freddie_Mac_Seller_Servicer_Guide",
        "url": "https://cdn.lhfs.com/lhfscdn/wholesale/download/FreddieMac_TheGuide.pdf",
        "description": "Freddie Mac Single-Family Seller/Servicer Guide",
    },
]

# Fannie Mae doesn't have a single PDF download — their guide is web-based.
# We'll handle Fannie Mae separately via web scraping in a future phase.
FANNIE_NOTE = """
NOTE: Fannie Mae Selling Guide is web-only at https://selling-guide.fanniemae.com/
It doesn't have a single downloadable PDF. Options:
1. Scrape the web version (structured HTML)
2. Use their API if available
3. Download section-by-section
This will be handled in Phase 2 of ingestion.
"""


def download_file(url: str, dest: Path, description: str) -> bool:
    """Download a file with progress indication."""
    if dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  ✓ Already exists: {dest.name} ({size_mb:.1f} MB)")
        return True

    print(f"  ↓ Downloading: {description}")
    print(f"    URL: {url}")

    try:
        resp = requests.get(url, stream=True, timeout=120, headers={
            "User-Agent": "Mozilla/5.0 (compatible; amp-gateway/1.0; guideline-research)"
        })
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = (downloaded / total) * 100
                    print(f"\r    Progress: {pct:.0f}% ({downloaded // 1024}K / {total // 1024}K)", end="")

        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"\n  ✓ Saved: {dest.name} ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"\n  ✗ Failed: {e}")
        if dest.exists():
            dest.unlink()
        return False


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Mortgage Underwriting Guidelines — Document Download")
    print("=" * 60)
    print()

    success = 0
    failed = 0

    for source in SOURCES:
        dest = DATA_DIR / f"{source['name']}.pdf"
        if download_file(source["url"], dest, source["description"]):
            success += 1
        else:
            failed += 1
        print()

    print("-" * 60)
    print(f"Results: {success} downloaded, {failed} failed")
    print()
    print("Fannie Mae note:")
    print(FANNIE_NOTE)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
