"""
Krude - Unified Database Loader (DuckDB & SQLite)
==============================================================
Loads all five core domain files into a single unified database:
1. headlines.csv -> `headlines` table
2. ofac.csv -> `ofac` table
3. routes_expanded.csv -> `routes` table
4. imports_long.csv -> `imports` table (melted long: month, country, volume_kbd)
5. suppliers.csv -> `suppliers` table (with crude quality penalty & max_liftable_kbd)

Provides fast analytical SQL queries, views, and dual DuckDB/SQLite storage.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List
import duckdb
import pandas as pd

try:
    from data.melt_imports import generate_wide_imports_csv, melt_wide_to_long
    from data.build_suppliers import build_suppliers_csv
    from data.build_routes import build_routes_csv
    from data.generate_reference_data import build_ofac_csv, build_headlines_csv
    from data.corridor_exposure import compute_corridor_exposure
except ImportError:
    from melt_imports import generate_wide_imports_csv, melt_wide_to_long
    from build_suppliers import build_suppliers_csv
    from build_routes import build_routes_csv
    from generate_reference_data import build_ofac_csv, build_headlines_csv
    from corridor_exposure import compute_corridor_exposure

DATA_DIR = Path(__file__).resolve().parent
DUCKDB_PATH = DATA_DIR / "energy_digital_twin.duckdb"
SQLITE_PATH = DATA_DIR / "energy_digital_twin.db"

def prepare_all_source_files():
    """Ensures all source CSV files are up to date."""
    print("[*] Preparing all source data files...")
    
    # 1. Imports (wide + melted long)
    w_path = DATA_DIR / "imports_wide.csv"
    if not w_path.exists():
        generate_wide_imports_csv(w_path)
    l_path = melt_wide_to_long(w_path, DATA_DIR / "imports_long.csv")
    
    # 2. Suppliers (quality adjustment + max liftable kbd)
    build_suppliers_csv(DATA_DIR / "suppliers.csv")
    
    # 3. Routes
    r_path = DATA_DIR / "routes_expanded.csv"
    if not r_path.exists():
        build_routes_csv(r_path)
        
    # 4. OFAC sanctions
    if not (DATA_DIR / "ofac.csv").exists():
        build_ofac_csv(DATA_DIR / "ofac.csv")
    
    # 5. Headlines
    if not (DATA_DIR / "headlines.csv").exists():
        build_headlines_csv(DATA_DIR / "headlines.csv")
    print("[OK] All source files verified.")

def load_duckdb(duckdb_path: Path = DUCKDB_PATH) -> duckdb.DuckDBPyConnection:
    """Loads all tables into single DuckDB database."""
    print(f"[*] Ingesting into DuckDB database: {duckdb_path}")
    
    # Connect
    con = duckdb.connect(str(duckdb_path))
    
    # Ingest 1. headlines
    con.execute("CREATE OR REPLACE TABLE headlines AS SELECT * FROM read_csv_auto(?, ignore_errors=true)", [str(DATA_DIR / "headlines.csv")])
    
    # Ingest 2. ofac
    con.execute("CREATE OR REPLACE TABLE ofac AS SELECT * FROM read_csv_auto(?, ignore_errors=true)", [str(DATA_DIR / "ofac.csv")])
    
    # Ingest 3. routes
    con.execute("CREATE OR REPLACE TABLE routes AS SELECT * FROM read_csv_auto(?, ignore_errors=true)", [str(DATA_DIR / "routes_expanded.csv")])
    
    # Ingest 4. imports (melted long table)
    con.execute("CREATE OR REPLACE TABLE imports AS SELECT * FROM read_csv_auto(?, ignore_errors=true)", [str(DATA_DIR / "imports_long.csv")])
    
    # Ingest 5. suppliers
    con.execute("CREATE OR REPLACE TABLE suppliers AS SELECT * FROM read_csv_auto(?, ignore_errors=true)", [str(DATA_DIR / "suppliers.csv")])
    
    # Ingest 6. spr_facilities (if exists)
    if (DATA_DIR / "spr_facilities.csv").exists():
        con.execute("CREATE OR REPLACE TABLE spr_facilities AS SELECT * FROM read_csv_auto(?, ignore_errors=true)", [str(DATA_DIR / "spr_facilities.csv")])
    
    # Create Analytics View: Landed Cost & Supplier Routing Matrix
    con.execute("""
    CREATE OR REPLACE VIEW v_landed_procurement_options AS
    SELECT 
        s.country,
        s.grade,
        s.api_gravity,
        s.sulphur_pct,
        s.sanctioned,
        s.quality_adj_usd_per_bbl,
        s.base_fob_usd_per_bbl,
        s.max_liftable_kbd,
        r.route_id,
        r.load_port AS origin_port,
        COALESCE(r.primary_discharge_port, 'Vadinar') AS dest_port,
        r.distance_km,
        r.transit_days,
        r.chokepoint,
        r.cost_usd_per_barrel AS freight_usd_per_bbl,
        ROUND(s.base_fob_usd_per_bbl + r.cost_usd_per_barrel + s.quality_adj_usd_per_bbl, 2) AS total_landed_cost_usd_bbl,
        r.capacity_kbd AS route_capacity_kbd
    FROM suppliers s
    JOIN routes r ON LOWER(TRIM(s.country)) = LOWER(TRIM(COALESCE(r.source_country, r.source)))
    """)

    # Print summary counts
    tables = ["headlines", "ofac", "routes", "imports", "suppliers"]
    print("\n--- DuckDB Table Statistics ---")
    for t in tables:
        count = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  Table `{t}`: {count} rows")
        
    con.close()
    
    # Compute and populate Lock 2 Corridor Exposure
    compute_corridor_exposure(duckdb_path)
    print(f"[OK] DuckDB database successfully populated at {duckdb_path}")
    return duckdb_path

def load_sqlite(sqlite_path: Path = SQLITE_PATH) -> Path:
    """Loads all tables into single SQLite database."""
    print(f"[*] Ingesting into SQLite database: {sqlite_path}")
    
    if sqlite_path.exists():
        sqlite_path.unlink()
        
    conn = sqlite3.connect(str(sqlite_path))
    
    # Read via pandas and write to sqlite
    for tbl, fname in [
        ("headlines", "headlines.csv"),
        ("ofac", "ofac.csv"),
        ("routes", "routes_expanded.csv"),
        ("imports", "imports_long.csv"),
        ("suppliers", "suppliers.csv")
    ]:
        df = pd.read_csv(DATA_DIR / fname)
        df.to_sql(tbl, conn, if_exists="replace", index=False)
        count = len(df)
        print(f"  SQLite Table `{tbl}`: {count} rows")
        
    # Sync corridor_exposure to SQLite from DuckDB
    try:
        con_duck = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        df_exp = con_duck.execute("SELECT * FROM corridor_exposure").df()
        df_exp.to_sql("corridor_exposure", conn, if_exists="replace", index=False)
        con_duck.close()
        print(f"  SQLite Table `corridor_exposure`: {len(df_exp)} rows")
    except Exception as e:
        print(f"  [WARN] Failed to sync corridor_exposure to SQLite: {e}")

    conn.close()
    print(f"[OK] SQLite database successfully populated at {sqlite_path}")
    return sqlite_path

def build_all():
    prepare_all_source_files()
    load_duckdb()
    load_sqlite()

if __name__ == "__main__":
    build_all()
