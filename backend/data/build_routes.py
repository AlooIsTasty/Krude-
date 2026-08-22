"""
Krude - Maritime Route Table Builder
==================================================
Real sea distances computed from `searoute` graph routing around landmasses;
Chokepoints detected from route geometry using bounding boxes and 20-point segment densification;
Automatic alternate routes generated per blockable chokepoint when detour exceeds +5%;
Freight cost computed via calibrated linear distance model + canal tolls + pipeline tariffs.
"""

import warnings
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

warnings.filterwarnings("ignore")
import searoute as sr

DATA_DIR = Path(__file__).resolve().parent

SPEED_KNOTS = 13.5      # laden VLCC average
PORT_DAYS   = 2.0       # load + discharge + waiting
FREIGHT_A   = 0.68      # $/bbl fixed base freight
FREIGHT_B   = 0.000216  # $/bbl per km (calibrated: Gulf->India ~$1.20, US Gulf->India ~$5.00)
CANAL_TOLL  = {"suez": 0.40, "panama": 0.55}

# Exact lat/lon bounding boxes for key global maritime passages:
# lon_min, lon_max, lat_min, lat_max
CHOKE_BOX = {
    "hormuz":            (55.9, 56.9, 26.1, 27.0),
    "bab_el_mandeb":     (42.8, 43.9, 12.0, 13.5),
    "suez":              (32.0, 33.1, 29.6, 31.5),
    "malacca":           (98.0, 104.5,  0.5,  6.5),
    "cape_of_good_hope": (14.0, 26.0, -38.5, -33.0),
    "panama":            (-80.0, -79.4, 8.8, 9.4),
    "danish_straits":    (10.0, 13.0, 54.5, 57.8),
    "bosporus":          (28.8, 29.3, 40.9, 41.3),
}

# Blockable passages supported by searoute restrictions
BLOCKABLE = ["ormuz", "babalmandab", "suez", "panama"]

def in_box(lon: float, lat: float, b: Tuple[float, float, float, float]) -> bool:
    """Checks if a (lon, lat) coordinate falls inside a bounding box."""
    return b[0] <= lon <= b[1] and b[2] <= lat <= b[3]

def tag_chokepoints(coords: List[List[float]]) -> List[str]:
    """
    Densifies every route segment into 20 sub-points and detects all crossed chokepoints.
    Eliminates manual tagging errors and guarantees consistency with computed distance.
    """
    hit = []
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        for t in range(21):  # 20 sub-segments per leg
            f = t / 20.0
            lon, lat = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
            for name, box in CHOKE_BOX.items():
                if name not in hit and in_box(lon, lat, box):
                    hit.append(name)
    order = list(CHOKE_BOX.keys())
    return sorted(hit, key=order.index)

def get_route(o: List[float], d: List[float], blocked: Tuple[str, ...] = ()) -> Optional[Tuple[float, List[List[float]]]]:
    """
    Queries `searoute` graph routing with restrictions.
    Returns (distance_km, coordinate_linestring) or None if no valid marine path exists.
    """
    try:
        r = sr.searoute(o, d, units="km", speed_knot=SPEED_KNOTS,
                        restrictions=["northwest", *blocked])
        km = r["properties"]["length"]
        if km <= 0:
            return None
        return km, r["geometry"]["coordinates"]
    except Exception:
        return None

def calculate_freight_cost(km: float, chokes: List[str], pipe_tariff: float) -> float:
    """
    Calibrated Linear Model:
    cost_usd_per_bbl = 0.68 + 0.000216 * distance_km + pipeline_tariff + canal_tolls
    """
    c = FREIGHT_A + FREIGHT_B * km + pipe_tariff
    for ch in chokes:
        c += CANAL_TOLL.get(ch, 0.0)
    return round(c, 2)

# Global Origins (country, port, lon, lat, pipe_tariff, route_cap_kbd, note)
ORIGINS = [
    ("Iraq",          "Basrah (BOT)",     48.80,  29.68, 0.00, None, "Main Iraqi Persian Gulf export terminal"),
    ("Iraq",          "Ceyhan",           35.88,  36.87, 1.00,  450, "Kirkuk-Ceyhan pipeline (design 1500, alloc 750, thru 200 kbd)"),
    ("Saudi Arabia",  "Ras Tanura",       50.16,  26.65, 0.00, None, "Primary Gulf terminal; vulnerable to Hormuz"),
    ("Saudi Arabia",  "Yanbu",            38.06,  24.09, 0.45, 7000, "East-West crude pipeline; bypasses Hormuz"),
    ("UAE",           "Jebel Dhanna",     52.60,  24.18, 0.00, None, "Abu Dhabi Persian Gulf coast terminal"),
    ("UAE",           "Fujairah",         56.36,  25.16, 0.30, 1800, "ADCOP pipeline terminal; outside Hormuz"),
    ("Kuwait",        "Mina al-Ahmadi",   48.15,  29.07, 0.00, None, "Kuwait Gulf export hub; no bypass exists"),
    ("Qatar",         "Ras Laffan",       51.55,  25.92, 0.00, None, "Condensate & LNG hub inside Hormuz"),
    ("Oman",          "Mina al-Fahal",    58.50,  23.64, 0.00, None, "Muscat coast; naturally outside Hormuz"),
    ("Iran",          "Kharg Island",     50.32,  29.23, 0.00, None, "Primary Iranian export terminal; sanctioned"),
    ("Russia",        "Primorsk",         28.72,  60.34, 0.00, None, "Baltic Sea Urals terminal"),
    ("Russia",        "Novorossiysk",     37.80,  44.72, 0.00, None, "Black Sea Urals/CPC terminal"),
    ("Russia",        "Kozmino",         132.13,  42.72, 0.00, None, "Pacific ESPO terminal transiting Malacca"),
    ("Nigeria",       "Bonny",             7.17,   4.42, 0.00, None, "West Africa light sweet crude"),
    ("Angola",        "Malongo",          11.50,  -7.00, 0.00, None, "Cabinda offshore medium sweet"),
    ("Brazil",        "Santos Basin",    -43.50, -24.50, 0.00, None, "Pre-salt Tupi / Buzios basin"),
    ("Venezuela",     "Jose",            -64.85,  10.10, 0.00, None, "Orinoco heavy sour terminal; sanctioned"),
    ("USA",           "Corpus Christi",  -97.20,  27.80, 0.00, None, "US Gulf Coast WTI export hub"),
    ("USA",           "Houston",         -94.80,  29.30, 0.00, None, "US Gulf Coast crude hub"),
    ("Libya",         "Es Sider",         18.36,  30.64, 0.00, None, "Mediterranean light sweet crude"),
    ("Guyana",        "Liza (offshore)", -57.00,   8.00, 0.00, None, "Guyana offshore Liza medium sweet"),
    ("Mexico",        "Cayo Arcas",      -92.00,  20.20, 0.00, None, "Gulf of Mexico Maya heavy crude"),
]

# Strategic Indian Import Destinations (Vadinar West Coast, Paradip East Coast)
DESTS = [
    ("Vadinar", 69.72, 22.35),
    ("Paradip", 86.68, 20.26)
]

def build_routes_csv(output_path: Path = DATA_DIR / "routes_expanded.csv") -> Path:
    """Computes real searoute network graph routes, detects chokepoints, and generates alternates."""
    rows = []
    print("[*] Calculating marine routes & geometric chokepoint intersections...")

    for (country, port, lon, lat, tariff, cap, note) in ORIGINS:
        o = [lon, lat]
        for (dname, dlon, dlat) in DESTS:
            d = [dlon, dlat]
            base = get_route(o, d)
            if base is None:
                print(f"  [WARN] No marine route from {port} -> {dname}")
                continue
            
            base_km, base_geom = base
            base_ch = tag_chokepoints(base_geom)
            
            variants = [("pipeline_bypass" if tariff > 0 else "direct", base_km, base_ch, base_geom)]
            
            # Test each blockable chokepoint to generate genuine alternates (>5% longer)
            for p in BLOCKABLE:
                alt = get_route(o, d, (p,))
                if alt is None:
                    continue
                km, geom = alt
                if km > base_km * 1.05:
                    alt_ch = tag_chokepoints(geom)
                    variants.append((f"avoid_{p}", km, alt_ch, geom))
                    
            for (rtype, km, chs, geom) in variants:
                transit_days = round(km / (SPEED_KNOTS * 1.852 * 24.0) + PORT_DAYS, 1)
                cost_bbl = calculate_freight_cost(km, chs, tariff)
                rows.append({
                    "source": country,
                    "origin_port": port,
                    "dest_port": dname,
                    "route_type": rtype,
                    "distance_km": int(round(km)),
                    "transit_days": transit_days,
                    "chokepoint": "|".join(chs) if chs else "none",
                    "cost_usd_per_barrel": cost_bbl,
                    "capacity_kbd": cap if cap else 9999,
                    "notes": note,
                    "geometry": json.dumps(geom)
                })

    # Deduplicate and sort
    seen = set()
    clean = []
    for r in rows:
        k = (r["origin_port"], r["dest_port"], r["distance_km"], r["route_type"])
        if k in seen:
            continue
        seen.add(k)
        clean.append(r)

    clean.sort(key=lambda r: (r["source"], r["dest_port"], r["distance_km"]))
    
    for i, r in enumerate(clean, 1):
        r["route_id"] = f"R{i:03d}"

    cols = [
        "route_id", "source", "origin_port", "dest_port", "route_type",
        "distance_km", "transit_days", "chokepoint", "cost_usd_per_barrel",
        "capacity_kbd", "notes", "geometry"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in clean:
            w.writerow(r)

    print(f"[OK] Generated {len(clean)} expanded maritime routes -> {output_path}")
    return output_path

if __name__ == "__main__":
    p = build_routes_csv()
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sample_rows = list(reader)[:6]
        print("\n--- routes_expanded.csv Sample ---")
        for r in sample_rows:
            print(f"[{r['route_id']}] {r['origin_port']} -> {r['dest_port']} ({r['route_type']}): {r['distance_km']} km, {r['transit_days']} days, chokes: {r['chokepoint']}, cost: ${r['cost_usd_per_barrel']}/bbl")
