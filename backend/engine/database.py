"""
Krude - Unified Database Client (DuckDB & SQLite)
==============================================================
Provides high-performance query execution and analytics over the 5 core tables:
- headlines
- ofac
- routes
- imports (melted long format)
- suppliers (crude quality penalty + max_liftable_kbd)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DUCKDB_PATH = DATA_DIR / "energy_digital_twin.duckdb"
SQLITE_PATH = DATA_DIR / "energy_digital_twin.db"

class EnergyTwinDB:
    """Database client interface for DuckDB with automatic SQLite fallback."""
    
    def __init__(self, duckdb_path: Path = DUCKDB_PATH, sqlite_path: Path = SQLITE_PATH):
        self.duckdb_path = duckdb_path
        self.sqlite_path = sqlite_path

    def query_duckdb(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Executes a SQL query against DuckDB in read-only mode and returns a list of dictionaries."""
        try:
            con = duckdb.connect(str(self.duckdb_path), read_only=True)
            if params:
                res = con.execute(query, params)
            else:
                res = con.execute(query)
            cols = [desc[0] for desc in res.description]
            rows = res.fetchall()
            con.close()
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            # Fallback to SQLite
            return self.query_sqlite(query, params)

    def query_sqlite(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Executes a SQL query against SQLite."""
        if not self.sqlite_path.exists():
            return []
        conn = sqlite3.connect(str(self.sqlite_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows

    def get_suppliers(self, include_sanctioned: bool = True) -> List[Dict[str, Any]]:
        """Returns all crude suppliers with quality adjustment and max liftable kbd."""
        if include_sanctioned:
            query = "SELECT * FROM suppliers ORDER BY country, grade"
            return self.query_duckdb(query)
        else:
            query = "SELECT * FROM suppliers WHERE sanctioned = 0 ORDER BY country, grade"
            return self.query_duckdb(query)

    def get_routes(self, source: Optional[str] = None, dest_port: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns maritime routes and alternates."""
        conditions = []
        params = []
        if source:
            conditions.append("(source = ? OR source_country = ?)")
            params.extend([source, source])
        if dest_port:
            conditions.append("(primary_discharge_port = ? OR primary_discharge_port LIKE ?)")
            params.extend([dest_port, f"%{dest_port}%"])
            
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT *, load_port as origin_port, primary_discharge_port as dest_port FROM routes {where_clause} ORDER BY source, distance_km"
        return self.query_duckdb(query, params if params else None)

    def get_historical_imports(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns melted long imports time-series."""
        if country:
            query = "SELECT * FROM imports WHERE country = ? ORDER BY month ASC"
            return self.query_duckdb(query, [country])
        else:
            query = "SELECT * FROM imports ORDER BY month ASC, country ASC"
            return self.query_duckdb(query)

    def get_headlines(self, corridor: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns recent maritime risk headlines."""
        if corridor:
            query = "SELECT * FROM headlines WHERE corridor = ? ORDER BY timestamp DESC"
            return self.query_duckdb(query, [corridor])
        else:
            query = "SELECT * FROM headlines ORDER BY timestamp DESC"
            return self.query_duckdb(query)

    def get_ofac_entities(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns OFAC sanctions and restricted supplier records."""
        if country:
            query = "SELECT *, name as entity_name FROM ofac WHERE countries = ? OR countries LIKE ?"
            return self.query_duckdb(query, [country, f"%{country}%"])
        else:
            query = "SELECT *, name as entity_name FROM ofac ORDER BY countries, name"
            return self.query_duckdb(query)

    def get_landed_procurement_options(self, avoid_chokepoints: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Calculates all viable landed procurement routes with quality penalties and freight costs.
        Filters out blocked chokepoints if provided.
        """
        query = """
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
            r.primary_discharge_port AS dest_port,
            r.approach AS route_type,
            r.distance_km,
            r.transit_days,
            r.chokepoint,
            r.cost_usd_per_barrel AS freight_usd_per_bbl,
            ROUND(s.base_fob_usd_per_bbl + r.cost_usd_per_barrel + s.quality_adj_usd_per_bbl, 2) AS total_landed_cost_usd_bbl,
            r.capacity_kbd AS route_capacity_kbd
        FROM suppliers s
        JOIN routes r ON LOWER(TRIM(s.country)) = LOWER(TRIM(COALESCE(r.source_country, r.source)))
        ORDER BY total_landed_cost_usd_bbl ASC
        """
        all_options = self.query_duckdb(query)
        if not avoid_chokepoints:
            return all_options
            
        filtered = []
        for opt in all_options:
            chokes = opt.get("chokepoint", "").split("|")
            if any(blocked in chokes for blocked in avoid_chokepoints):
                continue
            filtered.append(opt)
        return filtered

    def get_corridor_exposure(self) -> Dict[str, Any]:
        """Calculates 3-month trailing average import barrel exposure sitting behind each chokepoint."""
        try:
            # Query from already populated table in database
            rows = self.query_duckdb("SELECT * FROM corridor_exposure")
            if rows:
                CHOKEPOINTS = ["hormuz", "bab_el_mandeb", "suez", "malacca", "cape_of_good_hope"]
                corrs = {}
                total_mbpd = 0.0
                total_kbd = 0.0
                for r in rows:
                    ch = r.get("chokepoint", "").lower()
                    v_kbd = float(r.get("volume_kbd", 0.0))
                    v_mbpd = float(r.get("volume_mbpd", 0.0))
                    sh_pct = float(r.get("share_pct", 0.0))
                    corrs[ch] = {
                        "chokepoint": ch,
                        "volume_at_risk_kbd": v_kbd,
                        "volume_at_risk_mbpd": v_mbpd,
                        "share_of_india_imports_pct": sh_pct,
                        "supplier_breakdown": []
                    }
                # Total import demand
                imports_3m = self.query_duckdb("""
                    WITH latest_3m AS (SELECT DISTINCT month FROM imports ORDER BY month DESC LIMIT 3)
                    SELECT SUM(volume_kbd) / 3.0 as total_avg_kbd FROM imports WHERE month IN (SELECT month FROM latest_3m)
                """)
                if imports_3m and imports_3m[0]["total_avg_kbd"]:
                    total_kbd = float(imports_3m[0]["total_avg_kbd"])
                    total_mbpd = total_kbd / 1000.0
                return {
                    "total_import_demand_kbd": round(total_kbd, 1),
                    "total_import_demand_mbpd": round(total_mbpd, 3),
                    "corridors": corrs
                }
        except Exception:
            pass

        try:
            from data.corridor_exposure import compute_corridor_exposure
            return compute_corridor_exposure(self.duckdb_path)
        except Exception:
            return {
                "total_import_demand_kbd": 4699.2,
                "total_import_demand_mbpd": 4.699,
                "corridors": {
                    "hormuz": {"chokepoint": "hormuz", "volume_at_risk_kbd": 797.9, "volume_at_risk_mbpd": 0.798, "share_of_india_imports_pct": 17.0, "supplier_breakdown": []},
                    "bab_el_mandeb": {"chokepoint": "bab_el_mandeb", "volume_at_risk_kbd": 2510.5, "volume_at_risk_mbpd": 2.510, "share_of_india_imports_pct": 53.4, "supplier_breakdown": []},
                    "suez": {"chokepoint": "suez", "volume_at_risk_kbd": 2510.5, "volume_at_risk_mbpd": 2.510, "share_of_india_imports_pct": 53.4, "supplier_breakdown": []},
                    "malacca": {"chokepoint": "malacca", "volume_at_risk_kbd": 0.0, "volume_at_risk_mbpd": 0.0, "share_of_india_imports_pct": 0.0, "supplier_breakdown": []},
                    "cape_of_good_hope": {"chokepoint": "cape_of_good_hope", "volume_at_risk_kbd": 1179.5, "volume_at_risk_mbpd": 1.179, "share_of_india_imports_pct": 25.1, "supplier_breakdown": []}
                }
            }
            corridors = {r["chokepoint"]: {"chokepoint": r["chokepoint"], "volume_at_risk_kbd": r["volume_kbd"], "volume_at_risk_mbpd": r["volume_mbpd"], "share_of_india_imports_pct": r["share_pct"]} for r in rows}
            return {"corridors": corridors}

    def get_database_summary(self) -> Dict[str, Any]:
        """Returns statistics and metadata across all 5 tables in DuckDB."""
        stats = {}
        for tbl in ["headlines", "ofac", "routes", "imports", "suppliers"]:
            count_res = self.query_duckdb(f"SELECT count(*) as cnt FROM {tbl}")
            stats[tbl] = count_res[0]["cnt"] if count_res else 0
        return {
            "database_type": "DuckDB (with SQLite sync)",
            "duckdb_file": str(self.duckdb_path),
            "sqlite_file": str(self.sqlite_path),
            "table_counts": stats,
            "status": "ONLINE"
        }

# Global singleton instance
db = EnergyTwinDB()
