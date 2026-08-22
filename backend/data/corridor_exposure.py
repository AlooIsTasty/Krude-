"""
Krude - Lock 2: Corridor Exposure Calculation
===========================================================
Joins 3-month trailing average imports to routes on source country.
Computes the exact volume of India's barrels (in kbd and MBPD) sitting behind each chokepoint.
One number per chokepoint. Feeds the downstream impact model.
Sanity check: Hormuz lands near 40–48% of total Indian crude imports.
"""

import duckdb
from pathlib import Path
from typing import Dict, Any

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "energy_digital_twin.duckdb"

def compute_corridor_exposure(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Joins 3-month trailing avg imports to routes on source and computes barrels per chokepoint."""
    con = duckdb.connect(str(db_path))
    
    # 1. Join 3-month trailing average imports to maritime routes on source
    query = """
    WITH latest_3m AS (
        SELECT DISTINCT month FROM imports ORDER BY month DESC LIMIT 3
    ),
    trailing_3m AS (
        SELECT country, AVG(volume_kbd) AS avg_kbd
        FROM imports
        WHERE month IN (SELECT month FROM latest_3m)
        GROUP BY country
    ),
    country_exposure AS (
        SELECT t.country, t.avg_kbd, r.chokepoint
        FROM trailing_3m t
        JOIN (
            SELECT COALESCE(source_country, source) as src_country, chokepoint,
                   ROW_NUMBER() OVER (PARTITION BY COALESCE(source_country, source) ORDER BY (chokepoint != 'none') DESC, distance_km ASC) as rn
            FROM routes
        ) r ON LOWER(TRIM(t.country)) = LOWER(TRIM(r.src_country)) AND r.rn = 1
    )
    SELECT * FROM country_exposure
    """
    df = con.execute(query).df()
    total_kbd = float(df['avg_kbd'].sum())

    # 2. Compute barrels sitting behind each chokepoint (One number per chokepoint)
    CHOKEPOINTS = ["hormuz", "bab_el_mandeb", "suez", "malacca", "cape_of_good_hope"]
    choke_volumes = {ch: 0.0 for ch in CHOKEPOINTS}
    choke_suppliers = {ch: [] for ch in CHOKEPOINTS}

    for _, row in df.iterrows():
        c_name, vol, ch_str = row['country'], float(row['avg_kbd']), str(row['chokepoint'])
        for ch in ch_str.split('|'):
            if ch in choke_volumes:
                choke_volumes[ch] += vol
                choke_suppliers[ch].append({"country": c_name, "volume_kbd": round(vol, 1)})

    # 3. Format exposure metrics and save table for downstream impact model
    results = {}
    for ch in CHOKEPOINTS:
        v_kbd = choke_volumes[ch]
        pct = (v_kbd / total_kbd * 100.0) if total_kbd > 0 else 0.0
        results[ch] = {
            "chokepoint": ch,
            "volume_at_risk_kbd": round(v_kbd, 1),
            "volume_at_risk_mbpd": round(v_kbd / 1000.0, 3),
            "share_of_india_imports_pct": round(pct, 1),
            "supplier_breakdown": sorted(choke_suppliers[ch], key=lambda x: x["volume_kbd"], reverse=True)
        }

    con.execute("CREATE OR REPLACE TABLE corridor_exposure (chokepoint VARCHAR, volume_kbd DOUBLE, volume_mbpd DOUBLE, share_pct DOUBLE)")
    for ch, d in results.items():
        con.execute("INSERT INTO corridor_exposure VALUES (?, ?, ?, ?)", [ch, d["volume_at_risk_kbd"], d["volume_at_risk_mbpd"], d["share_of_india_imports_pct"]])

    con.close()
    return {
        "total_import_demand_kbd": round(total_kbd, 1),
        "total_import_demand_mbpd": round(total_kbd / 1000.0, 3),
        "corridors": results
    }

if __name__ == "__main__":
    res = compute_corridor_exposure()
    print("=" * 65)
    print("  INDIA CRUDE IMPORT CHOKEPOINT EXPOSURE (3-MONTH TRAILING AVG)")
    print("=" * 65)
    print(f"Total Daily Crude Imports: {res['total_import_demand_kbd']} kbd ({res['total_import_demand_mbpd']} MBPD)\n")
    print(f"{'Chokepoint':20s} | {'Volume (kbd)':12s} | {'Volume (MBPD)':14s} | {'Share of Imports':16s}")
    print("-" * 65)
    for ch, d in res['corridors'].items():
        print(f"{ch:20s} | {d['volume_at_risk_kbd']:10.1f} kbd | {d['volume_at_risk_mbpd']:10.3f} MBPD | {d['share_of_india_imports_pct']:14.1f} %")
    print("=" * 65)

