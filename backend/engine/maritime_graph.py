"""
Krude - Block 5: Maritime Supply Chain Graph (NetworkX)
====================================================================
Builds a directed graph representing global crude oil transit routes to India:
  Source Country -> Origin Port -> Chokepoint -> Destination Port (India)

Data Source: backend/data/routes_expanded.csv
"""

import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROUTES_CSV_PATH = DATA_DIR / "routes_expanded.csv"

class MaritimeSupplyGraph:
    """
    Directed Multi-layer Supply Chain Graph:
    Layer 1: Source Country (e.g., 'Saudi Arabia', 'Iraq', 'Russia', 'USA')
    Layer 2: Origin Load Port (e.g., 'Ras Tanura', 'Basrah Oil Terminal', 'Houston')
    Layer 3: Chokepoint / Maritime Transit (e.g., 'Hormuz', 'Bab-el-Mandeb', 'Suez', 'Cape of Good Hope', 'Malacca', 'Direct Sea')
    Layer 4: Indian Discharge Port / Refinery Terminal (e.g., 'Jamnagar', 'Vadinar', 'Paradip', 'Mangalore', 'Mundra', 'Kochi', 'Chennai')
    """
    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or ROUTES_CSV_PATH
        self.graph: nx.DiGraph = nx.DiGraph()
        self.routes_raw: List[Dict[str, Any]] = []
        self.build_graph()

    def build_graph(self) -> nx.DiGraph:
        """Constructs NetworkX DiGraph by iterating over rows of routes_expanded.csv."""
        self.graph.clear()
        self.routes_raw.clear()

        if not self.csv_path.exists():
            raise FileNotFoundError(f"Routes dataset not found at {self.csv_path}")

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.routes_raw.append(row)

                route_id = row.get("route_id", "")
                src_country = row.get("source_country", "").strip()
                load_port = row.get("load_port", "").strip()
                dest_port = row.get("primary_discharge_port", "").strip()
                chokepoint_raw = row.get("chokepoint", "none").strip()
                region = row.get("region", "")
                vessel_class = row.get("vessel_class", "VLCC")
                approach = row.get("approach", "west")

                # Numeric metrics
                try:
                    dist_km = float(row.get("distance_km", 0))
                    dist_nm = float(row.get("distance_nm", 0))
                    transit_days = float(row.get("transit_days", 0))
                    cost_usd = float(row.get("cost_usd_per_barrel", 0))
                    capacity_kbd = float(row.get("capacity_kbd", 0))
                except ValueError:
                    dist_km, dist_nm, transit_days, cost_usd, capacity_kbd = 0, 0, 0, 0, 0

                # 1. Add Nodes with Attributes
                country_node = f"Country:{src_country}"
                port_node = f"OriginPort:{load_port}"
                dest_node = f"DestPort:{dest_port}"

                self.graph.add_node(country_node, label=src_country, node_type="country", region=region)
                self.graph.add_node(port_node, label=load_port, node_type="origin_port", country=src_country, region=region)
                self.graph.add_node(dest_node, label=dest_port, node_type="dest_port", country="India", approach=approach)

                # Edge 1: Country -> Origin Port
                self.graph.add_edge(
                    country_node,
                    port_node,
                    edge_type="production_to_port",
                    capacity_kbd=capacity_kbd
                )

                # Handle multi-chokepoint sequences (e.g. suez|bab_el_mandeb) or single/none
                chokepoints = [c.strip() for c in chokepoint_raw.split("|") if c.strip()]
                if not chokepoints or chokepoints == ["none"]:
                    chokepoints = ["Direct Sea"]

                prev_node = port_node
                for idx, ck in enumerate(chokepoints):
                    ck_name = ck.replace("_", " ").title() if ck != "Direct Sea" else "Direct Open Sea"
                    ck_node = f"Chokepoint:{ck_name}"
                    self.graph.add_node(ck_node, label=ck_name, node_type="chokepoint")

                    # Edge from previous node to chokepoint
                    self.graph.add_edge(
                        prev_node,
                        ck_node,
                        edge_type="transit_leg",
                        route_id=route_id,
                        vessel_class=vessel_class,
                        distance_km=dist_km,
                        distance_nm=dist_nm,
                        transit_days=transit_days,
                        cost_usd_per_barrel=cost_usd,
                        capacity_kbd=capacity_kbd
                    )
                    prev_node = ck_node

                # Final Edge: Last Chokepoint -> Destination Port
                self.graph.add_edge(
                    prev_node,
                    dest_node,
                    edge_type="discharge_leg",
                    route_id=route_id,
                    approach=approach,
                    capacity_kbd=capacity_kbd
                )

        return self.graph

    def get_chokepoints(self) -> List[str]:
        """Returns all chokepoint node labels in the network graph."""
        return [
            data["label"] for node, data in self.graph.nodes(data=True)
            if data.get("node_type") == "chokepoint"
        ]

    def get_chokepoint_throughput(self) -> Dict[str, float]:
        """Calculates aggregate nameplate throughput (kbd) sitting behind each chokepoint."""
        throughput = {}
        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") == "chokepoint":
                label = data["label"]
                # Sum capacities of incoming transit edges
                total_kbd = sum(
                    edge_data.get("capacity_kbd", 0)
                    for u, v, edge_data in self.graph.in_edges(node, data=True)
                )
                throughput[label] = round(total_kbd, 1)
        return throughput

    def get_routes_through_chokepoint(self, chokepoint_query: str) -> List[Dict[str, Any]]:
        """Returns all supply routes traversing a given chokepoint."""
        ck_query_clean = chokepoint_query.lower().replace(" ", "").replace("-", "").replace("_", "")
        matched_routes = []
        for r in self.routes_raw:
            r_ck = r.get("chokepoint", "").lower().replace(" ", "").replace("-", "").replace("_", "")
            if ck_query_clean in r_ck:
                matched_routes.append(r)
        return matched_routes

    def find_bypass_routes(self, blocked_chokepoint: str) -> List[Dict[str, Any]]:
        """Finds all viable maritime crude routes that DO NOT traverse the blocked chokepoint."""
        ck_query_clean = blocked_chokepoint.lower().replace(" ", "").replace("-", "").replace("_", "")
        bypass = []
        for r in self.routes_raw:
            r_ck = r.get("chokepoint", "").lower().replace(" ", "").replace("-", "").replace("_", "")
            if ck_query_clean not in r_ck:
                bypass.append(r)
        return bypass

    def get_graph_summary(self) -> Dict[str, Any]:
        """Returns structural topology metrics of the supply chain network."""
        node_types = {}
        for _, data in self.graph.nodes(data=True):
            nt = data.get("node_type", "unknown")
            node_types[nt] = node_types.get(nt, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_breakdown": node_types,
            "chokepoints": self.get_chokepoints(),
            "chokepoint_throughput_kbd": self.get_chokepoint_throughput()
        }

if __name__ == "__main__":
    print("=" * 80)
    print("  BLOCK 5: MARITIME SUPPLY CHAIN NETWORKX GRAPH")
    print("  Topology: Source Country -> Origin Port -> Chokepoint -> Destination Port (India)")
    print("=" * 80)

    mg = MaritimeSupplyGraph()
    summary = mg.get_graph_summary()

    print(f"\n[+] Graph Built Successfully:")
    print(f"    Total Nodes: {summary['total_nodes']}")
    print(f"    Total Edges: {summary['total_edges']}")
    print(f"    Node Types:  {summary['node_breakdown']}")
    print(f"\n[+] Chokepoints Identified:")
    for ck, kbd in summary['chokepoint_throughput_kbd'].items():
        print(f"    - {ck:<24} | Throughput: {kbd:>8.1f} kbd (~{kbd/1000.0:.2f} MBPD)")

    # Sample Routing Query: Bypass Routes during Hormuz Closure
    hormuz_routes = mg.get_routes_through_chokepoint("Hormuz")
    bypass_routes = mg.find_bypass_routes("Hormuz")
    print(f"\n[+] Chokepoint Exposure Analysis:")
    print(f"    Routes traversing Hormuz:  {len(hormuz_routes)} routes")
    print(f"    Routes bypassing Hormuz:   {len(bypass_routes)} routes (e.g. Red Sea, Cape of Good Hope, Malacca, Duqm)")

    print("\n[+] Sample Source Country -> Destination Port Paths (First 3):")
    sample_nodes = [n for n, d in mg.graph.nodes(data=True) if d.get("node_type") == "country"][:3]
    for c_node in sample_nodes:
        dest_node = "DestPort:Jamnagar"
        try:
            paths = list(nx.all_simple_paths(mg.graph, c_node, dest_node, cutoff=4))
            if paths:
                print(f"    Path: {' -> '.join(paths[0])}")
        except Exception:
            pass

    print("\n" + "=" * 80)
