"""
Krude - Test Suite for Energy Security Digital Twin
================================================================
Validates:
1. Unified DuckDB & SQLite database loading across all 5 core tables.
2. Searoute maritime network distances & geometric chokepoint detection.
3. Crude quality adjustments (API/Sulphur penalties against Indian refinery baseline).
4. Melted long-format historical imports & 1.4x surge liftable caps.
5. Live multi-criteria procurement orchestrator & landed cost optimizer.
"""

import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from engine.database import db
from engine.procurement_orchestrator import AdaptiveProcurementOrchestrator
from engine.scenario_modeller import DisruptionScenarioModeller
from engine.spr_optimiser import StrategicReserveOptimiser
from data.build_suppliers import calculate_quality_penalty

class TestKrudeDigitalTwin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = backend_dir / "data"
        cls.procurement_orchestrator = AdaptiveProcurementOrchestrator(cls.data_dir)
        cls.scenario_modeller = DisruptionScenarioModeller()
        cls.spr_optimiser = StrategicReserveOptimiser()

    def test_database_tables_and_row_counts(self):
        """Tests that all 5 tables exist in DuckDB with expected records."""
        summary = db.get_database_summary()
        self.assertEqual(summary["status"], "ONLINE")
        counts = summary["table_counts"]
        
        self.assertGreaterEqual(counts.get("headlines", 0), 5, "Headlines table should have >=5 rows")
        self.assertGreaterEqual(counts.get("ofac", 0), 10, "OFAC table should have >=10 rows")
        self.assertGreaterEqual(counts.get("routes", 0), 50, "Routes table should have >=50 rows")
        self.assertGreaterEqual(counts.get("imports", 0), 200, "Imports table should have >=200 rows")
        self.assertGreaterEqual(counts.get("suppliers", 0), 15, "Suppliers table should have >=15 rows")

    def test_searoute_distances_and_anchors(self):
        """Validates real marine distances against published tanker routes."""
        routes = db.get_routes()
        self.assertGreaterEqual(len(routes), 50, "At least 50 routes must be loaded")
        
        # Anchor 1: Basrah -> Jamnagar / Vadinar
        basrah_route = next((r for r in routes if "Basrah" in r.get("load_port", "") or "Basrah" in r.get("source", "")), None)
        self.assertIsNotNone(basrah_route, "Basrah route must exist")
        self.assertAlmostEqual(basrah_route["distance_km"], 2630, delta=100)
        self.assertIn("hormuz", basrah_route["chokepoint"])

        # Anchor 2: Houston / USA -> India
        houston_route = next((r for r in routes if "Houston" in r.get("load_port", "") or "USA" in r.get("source", "")), None)
        self.assertIsNotNone(houston_route, "Houston/USA route must exist")
        self.assertGreaterEqual(houston_route["distance_km"], 15000)
        self.assertIn("cape_of_good_hope", houston_route["chokepoint"])

    def test_crude_quality_penalty_formula(self):
        """
        Validates quality penalty:
        quality_adj = 0.25*max(0, 32-API) + 0.30*max(0, S-2.0) + 0.10*max(0, API-38)
        """
        # Merey (16 API, 2.5% S) -> $4.15
        self.assertEqual(calculate_quality_penalty(16.0, 2.50), 4.15)

        # Maya (22 API, 3.3% S) -> $2.89
        self.assertEqual(calculate_quality_penalty(22.0, 3.30), 2.89)

        # Bonny Light (34 API, 0.15% S) -> $0.00
        self.assertEqual(calculate_quality_penalty(34.0, 0.15), 0.00)

        # Basrah Medium (29 API, 2.9% S) -> $1.02
        self.assertEqual(calculate_quality_penalty(29.0, 2.90), 1.02)

        # Murban (40 API, 0.75% S) -> 0.10*(40-38) = $0.20
        self.assertEqual(calculate_quality_penalty(40.0, 0.75), 0.20)

    def test_melted_long_imports_and_surge_headroom(self):
        """Validates that imports table is melted long and max_liftable_kbd has 1.4x surge headroom from real dataset."""
        suppliers = db.get_suppliers()
        russia = next(s for s in suppliers if s["country"] == "Russia" and s["grade"] == "Urals")
        self.assertAlmostEqual(russia["max_liftable_kbd"], 3922.8, places=1)

        iraq = next(s for s in suppliers if s["country"] == "Iraq" and s["grade"] == "Basrah Medium")
        self.assertAlmostEqual(iraq["max_liftable_kbd"], 1665.1, places=1)

    def test_adaptive_procurement_orchestrator(self):
        """Tests live multi-criteria ranking and landed cost allocation."""
        # Test 1: Multi-criteria ranking
        ranked = self.procurement_orchestrator.rank_suppliers({
            "Hormuz": 8.5,
            "Bab-el-Mandeb": 7.0,
            "Malacca": 2.0,
            "Cape of Good Hope": 1.5,
            "Suez": 4.0
        })
        self.assertIn("ranked_suppliers", ranked)
        self.assertEqual(len(ranked["ranked_suppliers"]), 5)
        self.assertIsNotNone(ranked["optimal_recommendation"])

        # Test 2: Multi-source procurement allocation plan
        plan = self.procurement_orchestrator.generate_procurement_plan(
            required_deficit_mbpd=1.5,
            blocked_chokepoints=["hormuz"],
            allow_sanctioned=False
        )
        self.assertGreater(plan["procured_volume_mbpd"], 0.0)
        self.assertGreaterEqual(len(plan["allocated_orders"]), 1)
        for order in plan["allocated_orders"]:
            self.assertNotIn("hormuz", order["chokepoints"].split("|"))
            self.assertGreater(order["total_landed_cost_usd_bbl"], 0.0)

    def test_corridor_exposure_lock_2(self):
        """
        Lock 2 Validation:
        - Join imports to routes on source
        - 3-month trailing average
        - 1 number per chokepoint
        """
        res = db.get_corridor_exposure()
        
        self.assertIn("corridors", res)
        self.assertIn("total_import_demand_kbd", res)
        self.assertGreaterEqual(res["total_import_demand_kbd"], 4000.0)
        
        corridors = res["corridors"]
        self.assertIn("hormuz", corridors)
        self.assertIn("bab_el_mandeb", corridors)
        self.assertIn("suez", corridors)
        self.assertIn("cape_of_good_hope", corridors)
        
        self.assertGreater(corridors["bab_el_mandeb"]["volume_at_risk_kbd"], 0.0)
        self.assertGreater(corridors["cape_of_good_hope"]["volume_at_risk_kbd"], 0.0)
        
    def test_risk_pipeline_lock_1(self):
        """
        Lock 1 Validation:
        - Dedupe → Time Decay → Noisy-OR → Momentum → Sanctions pipeline
        - 18-month historical threat curve P(t)
        - Verification that P(Hormuz) rises on known tension dates (Apr 2024, Oct 2024, Jan 2026)
        """
        from engine.risk_pipeline import RiskPipeline
        pipeline = RiskPipeline()
        
        # Test 1: Tension Peaks
        p_apr24 = pipeline.compute_corridor_probability("Hormuz", "2024-04-15")
        self.assertGreaterEqual(p_apr24["p_disruption"], 0.75, "April 2024 tensions must produce P >= 0.75")
        
        p_oct24 = pipeline.compute_corridor_probability("Hormuz", "2024-10-04")
        self.assertGreaterEqual(p_oct24["p_disruption"], 0.85, "October 2024 missile barrage must produce P >= 0.85")
        
        p_jan26 = pipeline.compute_corridor_probability("Hormuz", "2026-01-29")
        self.assertGreaterEqual(p_jan26["p_disruption"], 0.80, "January 2026 gunboat interdictions must produce P >= 0.80")

        # Test 2: Calm / De-escalation periods
        p_may24 = pipeline.compute_corridor_probability("Hormuz", "2024-06-01")
        self.assertLessEqual(p_may24["p_disruption"], 0.25, "Calm period in June 2024 must decay to P <= 0.25")
        
        p_jun25 = pipeline.compute_corridor_probability("Hormuz", "2025-06-25")
        self.assertLessEqual(p_jun25["p_disruption"], 0.20, "Calm period in June 2025 must decay to P <= 0.20")

        # Test 3: Plot Generation
        plot_path = self.data_dir / "hormuz_18m_risk_plot.png"
        res_plot = pipeline.generate_plot(plot_path, corridor="Hormuz")
        self.assertTrue(res_plot.exists(), "Plot image file must be generated")
        if plot_path.exists():
            plot_path.unlink()

    def test_llama_model_manager_and_status(self):
        """Validates AIModelManager configuration, model status, and headline analysis."""
        from engine.fine_tuning_adapter import AIModelManager
        models_dir = backend_dir / "models"
        mgr = AIModelManager(self.data_dir, models_dir)
        status = mgr.get_status()
        
        self.assertEqual(status["active_backend"], "OLLAMA")
        self.assertEqual(status["model_name"], "Krude-risk")
        self.assertEqual(status["model_source_path"], r"C:\models\Krude")
        self.assertEqual(status["acceleration_device"], "NVIDIA GeForce RTX 3050")
        
        # Test analysis output schema
        res = mgr.analyze_headline("IRGC forces seize foreign tanker in Strait of Hormuz")
        self.assertIn("risk_score", res)
        self.assertIn("reason", res)
        self.assertGreaterEqual(res["risk_score"], 0.0)
        self.assertLessEqual(res["risk_score"], 10.0)

    def test_block4_scenario_engine(self):
        """Validates Block 4 run_scenario CLI engine outputs."""
        from engine.scenario_modeller import run_scenario
        res = run_scenario("Hormuz", phi=0.5, duration_days=30)
        self.assertEqual(res["chokepoint"], "Hormuz")
        self.assertEqual(res["phi"], 0.5)
        self.assertEqual(res["duration_days"], 30)
        self.assertEqual(len(res["gap_kbd_by_day"]), 30)
        self.assertAlmostEqual(res["daily_gap_kbd"], 1299.2, delta=5.0)
        self.assertGreater(res["price_delta"], 10.0)
        self.assertGreater(res["import_bill_delta"], 1.5)

    def test_block5_maritime_graph(self):
        """Validates Block 5 NetworkX supply chain graph topology."""
        from engine.maritime_graph import MaritimeSupplyGraph
        mg = MaritimeSupplyGraph()
        summary = mg.get_graph_summary()
        self.assertGreater(summary["total_nodes"], 50)
        self.assertGreater(summary["total_edges"], 60)
        self.assertIn("Hormuz", summary["chokepoints"])
        self.assertIn("Cape Of Good Hope", summary["chokepoints"])
        
        # Test bypass routing
        bypass = mg.find_bypass_routes("Hormuz")
        self.assertGreater(len(bypass), 20)

    def test_block4_reserve_lp_optimization(self):
        """
        Validates Block 4 Strategic Petroleum Reserve LP Optimization:
        - Minimizes shortfall VoLL + opportunity cost
        - R_{t+1} = R_t - d_t
        - 0 <= d_t <= SPR_MAX_DRAW_KBD (450 kbd)
        - Adaptive safety floor R_t >= R_min + P_hormuz * tail_gap
        - Front-loaded drawdown tapering around Day 35 as Cape cargoes arrive
        """
        from engine.spr_optimiser import StrategicReserveOptimiser
        spr = StrategicReserveOptimiser(self.data_dir)
        res = spr.optimize_drawdown_lp(
            duration_days=60,
            gross_blocked_kbd=1930.0,
            p_hormuz=0.88,
            cape_arrival_day=35,
            cape_rerouted_kbd=1100.0
        )
        self.assertEqual(res["status"], "OPTIMAL")
        self.assertEqual(len(res["timeline"]), 60)
        
        # Test 1: Hydraulic Drawdown Bound (<= 450 kbd)
        for p in res["timeline"]:
            self.assertGreaterEqual(p["spr_drawdown_kbd"], 0.0)
            self.assertLessEqual(p["spr_drawdown_kbd"], 450.0 + 1e-5)
            self.assertGreaterEqual(p["remaining_spr_kb"], 18000.0) # Adaptive floor check
        
        # Test 2: Front-loaded drawdown on early crisis days
        early_draws = [p["spr_drawdown_kbd"] for p in res["timeline"][:20]]
        self.assertTrue(all(d == 450.0 for d in early_draws), "Early days must draw at maximum capacity")
        
        # Test 3: Tapering around and after day 35
        late_draws = [p["spr_drawdown_kbd"] for p in res["timeline"][40:]]
        self.assertLess(sum(late_draws), sum(early_draws), "Drawdown must taper as Cape cargoes arrive")

    def test_block6_assumptions_yaml(self):
        """Validates Block 6 assumptions.yaml structure and parameters."""
        import yaml
        yaml_path = self.data_dir / "assumptions.yaml"
        self.assertTrue(yaml_path.exists(), "assumptions.yaml must exist")
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        self.assertEqual(data["national_energy_baseline"]["total_crude_demand_mbpd"], 5.405)
        self.assertEqual(data["strategic_petroleum_reserve"]["baseline_spr_coverage_days"], 9.5)
        self.assertEqual(data["risk_pipeline_parameters"]["time_decay_half_life_days"], 7.0)

if __name__ == "__main__":
    unittest.main()
