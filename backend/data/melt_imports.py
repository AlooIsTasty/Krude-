"""
==================================================================
Melt the import table from wide (monthly columns) to long (month, country, volume_kbd).
Ensures unit consistency across all downstream joins, ML models, and procurement optimizers.
"""

import csv
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path(__file__).resolve().parent

# Sample 24-month historical import dataset (in kbd) across major crude suppliers to India
# Spans 2024-07 through 2026-06 (24 months)
MONTHS = [
    "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
    "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
    "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12",
    "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"
]

# Baseline monthly historical volumes in kbd for major supplier nations to India
# Reflects realistic volumes: Russia (~1600-1950 kbd), Iraq (~900-1100 kbd), Saudi Arabia (~650-850 kbd),
# UAE (~350-550 kbd), USA (~200-380 kbd), Kuwait (~180-280 kbd), Nigeria (~100-220 kbd), Angola (~80-160 kbd),
# Oman (~60-140 kbd), Qatar (~50-110 kbd), Brazil (~40-95 kbd), Mexico (~30-80 kbd), Guyana (~20-60 kbd),
# Libya (~10-50 kbd), Venezuela (~0-80 kbd), Iran (~0 kbd due to sanctions)
BASE_VOLUMES_KBD = {
    "Russia":       [1750, 1820, 1790, 1850, 1920, 1880, 1910, 1840, 1890, 1950, 1920, 1870, 1860, 1890, 1820, 1850, 1900, 1940, 1910, 1860, 1880, 1920, 1890, 1850],
    "Iraq":         [980, 1020, 950, 1010, 1040, 990, 1050, 980, 1030, 1070, 1010, 990, 1020, 1060, 970, 1010, 1030, 1080, 1040, 990, 1010, 1050, 1020, 980],
    "Saudi Arabia": [720, 750, 690, 740, 780, 760, 810, 740, 790, 830, 770, 750, 760, 800, 730, 770, 790, 840, 800, 760, 770, 810, 780, 750],
    "UAE":          [420, 450, 410, 460, 480, 440, 490, 430, 470, 520, 460, 450, 470, 510, 440, 480, 500, 530, 490, 460, 470, 510, 480, 450],
    "USA":          [260, 290, 240, 280, 310, 270, 330, 260, 300, 350, 290, 280, 300, 340, 270, 310, 320, 360, 330, 290, 300, 340, 320, 290],
    "Kuwait":       [210, 230, 190, 220, 250, 220, 260, 210, 240, 270, 230, 220, 240, 260, 210, 230, 240, 270, 250, 220, 230, 260, 240, 220],
    "Nigeria":      [140, 160, 130, 150, 170, 140, 180, 140, 160, 190, 150, 140, 150, 180, 130, 160, 170, 190, 170, 150, 150, 180, 160, 140],
    "Angola":       [110, 120, 100, 115, 130, 110, 140, 105, 125, 150, 120, 110, 120, 135, 105, 120, 125, 145, 130, 115, 120, 135, 125, 110],
    "Oman":         [85, 95, 80, 90, 105, 85, 110, 80, 95, 115, 90, 85, 90, 105, 80, 95, 100, 115, 105, 90, 95, 105, 100, 85],
    "Qatar":        [70, 80, 65, 75, 85, 70, 90, 70, 80, 95, 75, 70, 75, 90, 65, 80, 85, 95, 85, 75, 80, 90, 85, 70],
    "Brazil":       [60, 70, 55, 65, 75, 60, 80, 60, 70, 85, 65, 60, 65, 80, 55, 70, 75, 85, 75, 65, 70, 80, 75, 60],
    "Mexico":       [45, 55, 40, 50, 60, 45, 65, 45, 55, 70, 50, 45, 50, 65, 40, 55, 60, 70, 60, 50, 55, 65, 60, 45],
    "Guyana":       [35, 40, 30, 38, 45, 35, 50, 32, 40, 55, 38, 35, 38, 48, 30, 40, 42, 52, 45, 38, 40, 48, 42, 35],
    "Libya":        [25, 30, 20, 28, 35, 25, 40, 22, 30, 45, 28, 25, 28, 38, 20, 30, 32, 42, 35, 28, 30, 38, 32, 25],
    "Venezuela":    [20, 30, 15, 0, 40, 0, 50, 0, 25, 60, 0, 0, 30, 50, 0, 20, 35, 60, 0, 15, 25, 45, 0, 20],
    "Iran":         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
}

def generate_wide_imports_csv(output_path: Path = DATA_DIR / "imports_wide.csv") -> Path:
    """Generates the wide-format historical crude import CSV."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["country"] + MONTHS)
        for country, vols in BASE_VOLUMES_KBD.items():
            writer.writerow([country] + vols)
    print(f"[OK] Generated wide imports: {output_path} ({len(BASE_VOLUMES_KBD)} countries x {len(MONTHS)} months)")
    return output_path

MONTH_MAP = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
}

def parse_month_to_iso(m_str: str) -> str:
    """Converts 'Apr-2024' or '2024-04' to '2024-04'."""
    m_str = m_str.strip()
    if "-" in m_str:
        parts = m_str.split("-")
        if len(parts) == 2:
            p1, p2 = parts[0], parts[1]
            if p1 in MONTH_MAP and len(p2) == 4:
                return f"{p2}-{MONTH_MAP[p1]}"
            elif p2 in MONTH_MAP and len(p1) == 4:
                return f"{p1}-{MONTH_MAP[p2]}"
            elif len(p1) == 4 and len(p2) == 2:
                return f"{p1}-{p2}"
    return m_str

def melt_wide_to_long(wide_path: Path = DATA_DIR / "imports_wide.csv",
                       output_path: Path = DATA_DIR / "imports_long.csv") -> Path:
    """
    Melts wide format imports CSV into long format:
    Columns: month (YYYY-MM), country, volume_kbd
    Supports both row-per-month and row-per-country schemas.
    """
    if not wide_path.exists():
        generate_wide_imports_csv(wide_path)

    long_rows = []
    with open(wide_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = [h.strip() for h in next(reader)]

        # Determine schema: row-per-month (starts with month,fiscal_year,...) vs row-per-country (starts with country,2024-07,...)
        if "month" in headers[0].lower():
            # Row-per-month schema (Real India trade dataset)
            # Find country columns (exclude metadata columns)
            exclude_cols = {"month", "fiscal_year", "listed total", "total supply", "india domestic"}
            country_indices = [
                (i, h) for i, h in enumerate(headers)
                if h.lower() not in exclude_cols
            ]

            for row in reader:
                if not row or not row[0].strip():
                    continue
                raw_month = row[0]
                iso_month = parse_month_to_iso(raw_month)
                
                # Determine number of days in month for daily kbd conversion
                days_in_month = 30.0
                try:
                    parts = raw_month.split("-")
                    m_name = parts[0] if parts[0] in MONTH_MAP else parts[1]
                    if m_name in ["Jan", "Mar", "May", "Jul", "Aug", "Oct", "Dec"]:
                        days_in_month = 31.0
                    elif m_name in ["Apr", "Jun", "Sep", "Nov"]:
                        days_in_month = 30.0
                    elif m_name == "Feb":
                        days_in_month = 28.25
                except Exception:
                    days_in_month = 30.0

                for idx, c_name in country_indices:
                    if idx < len(row):
                        val_str = row[idx].strip().replace(",", "")
                        try:
                            monthly_thousand_bbl = float(val_str)
                            # Convert thousand barrels/month to daily thousand barrels/day (kbd)
                            daily_kbd = round(monthly_thousand_bbl / days_in_month, 2)
                        except ValueError:
                            daily_kbd = 0.0

                        # Map names
                        clean_country = "Other Suppliers" if c_name.lower().startswith("others") else c_name

                        long_rows.append({
                            "month": iso_month,
                            "country": clean_country,
                            "volume_kbd": daily_kbd
                        })
        else:
            # Row-per-country schema
            month_cols = headers[1:]
            for row in reader:
                if not row or not row[0].strip():
                    continue
                country = row[0].strip()
                for month_name, val_str in zip(month_cols, row[1:]):
                    try:
                        val = float(val_str.strip().replace(",", ""))
                    except ValueError:
                        val = 0.0
                    long_rows.append({
                        "month": parse_month_to_iso(month_name),
                        "country": country,
                        "volume_kbd": round(val, 2)
                    })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["month", "country", "volume_kbd"])
        writer.writeheader()
        for r in long_rows:
            writer.writerow(r)

    print(f"[OK] Generated melted long imports: {output_path} ({len(long_rows)} rows)")
    return output_path

def compute_max_liftable_kbd(long_path: Path = DATA_DIR / "imports_long.csv") -> Dict[str, float]:
    """
    Calculates max liftable kbd per country:
    max_liftable_i = 1.4 * (highest monthly volume from country i in the last 24 months)
    """
    if not long_path.exists():
        melt_wide_to_long(output_path=long_path)

    max_historical: Dict[str, float] = {}
    with open(long_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            c = r["country"]
            vol = float(r["volume_kbd"])
            if c not in max_historical or vol > max_historical[c]:
                max_historical[c] = vol

    # Apply 1.4x surge headroom factor
    max_liftable = {c: round(1.4 * peak_vol, 1) for c, peak_vol in max_historical.items()}
    return max_liftable

if __name__ == "__main__":
    w_path = DATA_DIR / "imports_wide.csv"
    l_path = melt_wide_to_long(w_path)
    liftable = compute_max_liftable_kbd(l_path)
    print("\n--- Computed Max Liftable kbd (1.4x peak surge headroom from real dataset) ---")
    for country, cap in sorted(liftable.items(), key=lambda x: x[1], reverse=True):
        print(f"  {country:20s}: {cap:7.1f} kbd")

