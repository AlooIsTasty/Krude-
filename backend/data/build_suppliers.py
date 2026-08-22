"""
Krude - Supplier Reference Table Builder
======================================================
Builds suppliers.csv with crude quality penalties against Indian refinery baseline
(API ~32, Sulphur ~2.0%) and joins 24-month peak import volume with 1.4x surge headroom.

Quality Adjustment Formula:
quality_adj = 0.25 * max(0, 32 - API) + 0.30 * max(0, S - 2.0) + 0.10 * max(0, API - 38)
"""

import csv
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from data.melt_imports import compute_max_liftable_kbd
except ImportError:
    from melt_imports import compute_max_liftable_kbd

DATA_DIR = Path(__file__).resolve().parent

# (country, grade, api_gravity, sulphur_pct, sanctioned(0/1), base_fob_usd_bbl)
SUPPLIER_GRADES = [
    ("Iraq",              "Basrah Medium",       29.0, 2.90, 0, 78.50),
    ("Saudi Arabia",      "Arab Light",          33.0, 1.90, 0, 82.00),
    ("UAE",               "Murban",              40.0, 0.75, 0, 84.50),
    ("Kuwait",            "Kuwait Export",       31.0, 2.60, 0, 79.50),
    ("Qatar",             "Qatar Marine",        36.0, 1.40, 0, 81.00),
    ("Oman",              "Oman Export",         33.0, 1.10, 0, 82.50),
    ("Iran",              "Iranian Heavy",       30.0, 1.80, 1, 65.00),
    ("Russia",            "Urals",               31.0, 1.50, 1, 68.50),
    ("Russia",            "ESPO",                35.0, 0.60, 1, 74.00),
    ("Nigeria",           "Bonny Light",         34.0, 0.15, 0, 85.50),
    ("Angola",            "Girassol",            32.0, 0.30, 0, 83.50),
    ("Angola",            "Cabinda",             31.5, 0.40, 0, 82.00),
    ("Brazil",            "Tupi",                30.0, 0.35, 0, 81.50),
    ("Brazil",            "Buzios",              28.0, 0.30, 0, 80.00),
    ("Venezuela",         "Merey",               16.0, 2.50, 1, 58.00),
    ("USA",               "WTI Midland",         40.0, 0.35, 0, 83.00),
    ("USA",               "Mars Blend",          29.0, 1.80, 0, 79.00),
    ("Libya",             "Es Sider",            37.0, 0.45, 0, 84.00),
    ("Guyana",            "Liza",                32.0, 0.50, 0, 82.00),
    ("Mexico",            "Maya",                22.0, 3.30, 0, 71.00),
    ("Canada",            "Cold Lake / WCS",     21.0, 3.50, 0, 66.00),
    ("Colombia",          "Castilla / Vasconia", 19.0, 1.90, 0, 72.00),
    ("Ecuador",           "Oriente",             24.0, 1.50, 0, 73.50),
    ("Norway",            "Johan Sverdrup",      28.0, 0.80, 0, 82.00),
    ("Algeria",           "Saharan Blend",       44.0, 0.10, 0, 86.00),
    ("Egypt",             "Belayim",             27.5, 2.20, 0, 77.00),
    ("Sudan",             "Nile Blend",          33.0, 0.05, 0, 81.50),
    ("Azerbaijan",        "Azeri Light",         35.0, 0.15, 0, 85.00),
    ("Kazakhstan",        "CPC Blend",           45.0, 0.55, 0, 80.50),
    ("Malaysia",          "Kimanis",             36.0, 0.10, 0, 86.50),
    ("Australia",         "North West Shelf",    54.0, 0.02, 0, 84.00),
    ("Congo",             "Djeno",               27.5, 0.30, 0, 79.00),
    ("Gabon",             "Rabi Light",          33.0, 0.10, 0, 83.00),
    ("Cameroon",          "Kole",                31.0, 0.35, 0, 81.00),
    ("Equatorial Guinea", "Zafiro",              30.0, 0.25, 0, 82.50),
]

def calculate_quality_penalty(api: float, sulphur: float) -> float:
    """
    Indian refinery design slate ~ API 32, sulphur 2.0%
    - Heavy crude penalty ($0.25/bbl per deg API below 32): yield loss
    - Extra sour penalty ($0.30/bbl per % sulphur above 2.0%): hydrotreating / desulfurization cost
    - Too light penalty ($0.10/bbl per deg API above 38): poor middle distillate yield
    """
    penalty = (
        0.25 * max(0.0, 32.0 - api) +
        0.30 * max(0.0, sulphur - 2.0) +
        0.10 * max(0.0, api - 38.0)
    )
    return round(penalty, 2)

def build_suppliers_csv(output_path: Path = DATA_DIR / "suppliers.csv") -> Path:
    """Builds and writes suppliers.csv with quality adjustment and max liftable kbd."""
    liftable_map = compute_max_liftable_kbd(DATA_DIR / "imports_long.csv")
    
    rows = []
    for (country, grade, api, s, sanctioned, fob) in SUPPLIER_GRADES:
        qual_adj = calculate_quality_penalty(api, s)
        max_lift = liftable_map.get(country, 0.0)
        rows.append({
            "country": country,
            "grade": grade,
            "api_gravity": api,
            "sulphur_pct": s,
            "sanctioned": sanctioned,
            "quality_adj_usd_per_bbl": qual_adj,
            "base_fob_usd_per_bbl": fob,
            "max_liftable_kbd": max_lift
        })

    cols = [
        "country", "grade", "api_gravity", "sulphur_pct", "sanctioned",
        "quality_adj_usd_per_bbl", "base_fob_usd_per_bbl", "max_liftable_kbd"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"[OK] Generated suppliers table: {output_path} ({len(rows)} grades)")
    return output_path

if __name__ == "__main__":
    p = build_suppliers_csv()
    with open(p, "r", encoding="utf-8") as f:
        print("\n--- suppliers.csv Preview ---")
        print(f.read())
