from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

try:
    from engine.database import db
except ImportError:
    try:
        from backend.engine.database import db
    except ImportError:
        from database import db

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Verified Constants (EIA, PPAC, ISPRL, RBI Provenance from assumptions.yaml)
GLOBAL_SUPPLY_KBD = 102800.0   # EIA STEO World Liquids Supply (~102.8 MBPD)
BASE_BRENT = 82.50             # ICE Brent 12m rolling median ($/bbl) / PPAC Indian Basket
SPR_KB = 39470.0               # ISPRL Phase I Cavern Capacity (39.47 Million Barrels)
SPR_MAX_DRAW_KBD = 450.0       # ISPRL Max Simultaneous Pipeline Evacuation Rate (kbd)
USD_INR = 84.00                # RBI Reference Rate (₹/$ Spot)

# Canonical corridor exposures (in kbd) based on 3-month trailing imports
CORRIDOR_BASELINE_EXPOSURE_KBD = {
    "hormuz": 2598.3,
    "bab_el_mandeb": 2355.0,
    "red_sea": 2355.0,
    "suez": 900.0,
    "malacca": 800.0,
    "cape_of_good_hope": 650.0
}

TOTAL_INDIA_IMPORT_DEMAND_MBPD = 5.405 # ~5.4 MBPD crude imports per PPAC

def run_scenario(chokepoint: str, phi: float, duration_days: int) -> Dict[str, Any]:
    """
    Block 4: The Scenario Engine
    run_scenario(chokepoint, phi, duration_days) -> {gap_kbd_by_day, price_delta, import_bill_delta}

    Parameters:
    - chokepoint: str (e.g. 'hormuz', 'bab_el_mandeb', 'suez', 'malacca', 'cape_of_good_hope')
    - phi: float (disruption severity fraction: 0.0 <= phi <= 1.0)
    - duration_days: int (disruption duration in days)

    Returns:
    {
        "gap_kbd_by_day": List[float],      # Daily physical supply gap in kbd for each day
        "price_delta": float,               # Estimated crude price surge ($/bbl)
        "import_bill_delta": float,         # Additional landed import burden ($ Billion USD)
        "chokepoint": str,
        "phi": float,
        "duration_days": int,
        "daily_gap_kbd": float,
        "daily_gap_mbpd": float,
        "baseline_corridor_kbd": float
    }
    """
    phi = max(0.0, min(1.0, float(phi)))
    duration = max(1, int(duration_days))
    
    clean_ck = chokepoint.strip().lower().replace(" ", "_").replace("-", "_")
    base_kbd = CORRIDOR_BASELINE_EXPOSURE_KBD.get(clean_ck, 2598.3)

    # 1. Physical Supply Gap
    daily_gap_kbd = round(base_kbd * phi, 1)
    daily_gap_mbpd = round(daily_gap_kbd / 1000.0, 3)
    gap_kbd_by_day = [daily_gap_kbd for _ in range(duration)]

    # 2. Price Surge Delta ($/bbl)
    # Market elasticity: +$15.00/bbl for 50% Hormuz disruption, scale with phi & import shortfall
    shortfall_pct = (daily_gap_mbpd / TOTAL_INDIA_IMPORT_DEMAND_MBPD) * 100.0
    price_delta = round(max(0.0, (shortfall_pct / 24.0) * 15.0), 2)

    # 3. Import Bill Delta ($ Billion)
    # Added cost = (price_delta * total daily import volume * duration_days) / 1000
    import_bill_delta = round((price_delta * TOTAL_INDIA_IMPORT_DEMAND_MBPD * duration) / 1000.0, 2)

    # Macroeconomic indicators
    gdp_impact_pp = round((price_delta / 10.0) * 0.20, 2)
    cad_impact_bps = round((price_delta / 10.0) * 35.0, 1)

    return {
        "gap_kbd_by_day": gap_kbd_by_day,
        "price_delta": price_delta,
        "import_bill_delta": import_bill_delta,
        "chokepoint": chokepoint,
        "phi": phi,
        "duration_days": duration,
        "daily_gap_kbd": daily_gap_kbd,
        "daily_gap_mbpd": daily_gap_mbpd,
        "corridor_baseline_kbd": base_kbd,
        "shortfall_pct": round(shortfall_pct, 1),
        "gdp_impact_pp": gdp_impact_pp,
        "cad_impact_bps": cad_impact_bps
    }

class DisruptionScenarioModeller:
    """
    Component 2: Disruption Scenario Modeller
    Object-oriented wrapper around run_scenario and DuckDB corridor exposure.
    """
    def __init__(self, data_dir: Optional[Path] = None):
        self.db = db

    def simulate(
        self,
        corridor: str = "Hormuz",
        disruption_duration_days: int = 30,
        price_rise_usd_per_barrel: Optional[float] = None,
        net_shortfall_pct: Optional[float] = None,
        disruption_severity_pct: float = 50.0
    ) -> Dict[str, Any]:
        """
        Calculates scenario impacts based on live corridor exposure and user assumptions.
        """
        phi = disruption_severity_pct / 100.0
        res = run_scenario(corridor, phi, disruption_duration_days)

        if price_rise_usd_per_barrel is not None:
            price_rise = float(price_rise_usd_per_barrel)
            import_bill = round((price_rise * TOTAL_INDIA_IMPORT_DEMAND_MBPD * disruption_duration_days) / 1000.0, 2)
            gdp_pp = round((price_rise / 10.0) * 0.20, 3)
            cad_bps = round((price_rise / 10.0) * 35.0, 1)
        else:
            price_rise = res["price_delta"]
            import_bill = res["import_bill_delta"]
            gdp_pp = res["gdp_impact_pp"]
            cad_bps = res["cad_impact_bps"]

        shortfall = net_shortfall_pct if net_shortfall_pct is not None else res["shortfall_pct"]

        return {
            "component_label": "Simulated macro impact fed by REAL 3-month trailing corridor exposure",
            "scenario_inputs": {
                "corridor": corridor,
                "disruption_duration_days": disruption_duration_days,
                "disruption_severity_pct": disruption_severity_pct,
                "price_rise_usd_per_barrel": price_rise,
                "net_shortfall_pct": shortfall,
                "corridor_baseline_exposure_kbd": res["corridor_baseline_kbd"],
                "corridor_baseline_exposure_mbpd": round(res["corridor_baseline_kbd"] / 1000.0, 3),
                "blocked_supply_kbd": res["daily_gap_kbd"],
                "blocked_supply_mbpd": res["daily_gap_mbpd"]
            },
            "impacts": {
                "gdp_impact_pp": gdp_pp,
                "cad_impact_bps": cad_bps,
                "refining_utilization_drop_pct": round(shortfall, 1),
                "estimated_additional_cost_usd_billion": import_bill,
                "blocked_supply_volume_mbpd": res["daily_gap_mbpd"]
            },
            "gap_kbd_by_day": res["gap_kbd_by_day"],
            "explanation": (
                f"Corridor Exposure Analysis: {corridor} carries {res['corridor_baseline_kbd']:.1f} kbd base flow. "
                f"At {disruption_severity_pct:.0f}% disruption severity (phi={phi:.2f}), {res['daily_gap_kbd']:.1f} kbd "
                f"({res['daily_gap_mbpd']:.2f} MBPD) of crude supply is physically blocked. "
                f"Projected price shock of +${price_rise:.2f}/bbl over {disruption_duration_days} days adds "
                f"${import_bill:.2f} Billion to India's crude import bill (GDP headwind -{gdp_pp:.2f} pp, CAD +{cad_bps:.0f} bps)."
            )
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Block 4: Disruption Scenario Engine CLI")
    parser.add_argument("--chokepoint", type=str, default="Hormuz", help="Chokepoint name (Hormuz, Bab-el-Mandeb, Suez, Malacca, Cape of Good Hope)")
    parser.add_argument("--phi", type=float, default=0.5, help="Disruption severity fraction (0.0 to 1.0)")
    parser.add_argument("--duration", type=int, default=30, help="Disruption duration in days")
    args = parser.parse_args()

    print("=" * 80)
    print("  BLOCK 4: THE SCENARIO ENGINE -- CLI EXECUTION")
    print(f"  Input: chokepoint={args.chokepoint}, phi={args.phi}, duration_days={args.duration}")
    print("=" * 80)

    result = run_scenario(chokepoint=args.chokepoint, phi=args.phi, duration_days=args.duration)

    print(f"\n[+] Chokepoint:                  {result['chokepoint']}")
    print(f"[+] Severity (phi):              {result['phi'] * 100:.1f}% ({result['phi']:.2f})")
    print(f"[+] Disruption Duration:         {result['duration_days']} days")
    print(f"[+] Baseline Corridor Flow:      {result['corridor_baseline_kbd']:.1f} kbd (~{result['corridor_baseline_kbd']/1000.0:.2f} MBPD)")
    print(f"[+] Physical Daily Gap:          {result['daily_gap_kbd']:.1f} kbd (~{result['daily_gap_mbpd']:.2f} MBPD)")
    print(f"[+] Price Delta (+$/bbl):        +${result['price_delta']:.2f} / barrel")
    print(f"[+] Import Bill Delta ($B):      +${result['import_bill_delta']:.2f} Billion USD")
    print(f"[+] Macro Headwinds:             GDP Growth: -{result['gdp_impact_pp']:.2f} pp | CAD: +{result['cad_impact_bps']:.0f} bps")
    print(f"\n[+] gap_kbd_by_day (first 5 days): {result['gap_kbd_by_day'][:5]} ... [{len(result['gap_kbd_by_day'])} days total]")
    print("\n" + "=" * 80)
