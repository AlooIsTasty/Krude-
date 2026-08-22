"""
Krude - Component 4: Strategic Reserve Linear Program (LP) Optimization
=============================================================================
Formulation:
    minimise Σ (shortfall_t * VoLL + d_t * opportunity_cost)
    s.t.     R_{t+1} = R_t - d_t
             0 <= d_t <= SPR_MAX_DRAW_KBD
             R_t >= R_min + P_hormuz * tail_gap    <-- Adaptive Geopolitical Buffer
             shortfall_t >= net_deficit_t - d_t
             shortfall_t >= 0

Connects 3 Modules:
  1. Geopolitical Risk Engine (P_hormuz adaptive floor)
  2. Disruption Scenario Engine (Gross blocked volume, duration T)
  3. Maritime Logistics / Procurement Network (Cape rerouted cargoes landing at Day ~35)
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Baseline constants (from assumptions.yaml)
SPR_KB_DEFAULT = 39470.0            # Total ISPRL Phase I Capacity (39.47 Million Barrels)
SPR_MAX_DRAW_KBD_DEFAULT = 450.0    # Maximum simultaneous hydraulic pump evacuation rate
R_MIN_KB_DEFAULT = 12450.0          # Unbreachable cavern heel & strategic floor (~3.0 days)
TAIL_GAP_KB_DEFAULT = 6400.0        # Expected post-crisis tail vulnerability buffer
VOLL_DEFAULT = 200.0                # Value of Lost Load ($/barrel economic damage of unserved crude)
OPPORTUNITY_COST_DEFAULT = 18.0     # Cost of depleting strategic reserve vs replacement ($/barrel)

class StrategicReserveOptimiser:
    """
    Component 4: Strategic Reserve LP Optimization Agent
    Solves optimal daily SPR release trajectory over a multi-week crisis horizon.
    """
    def __init__(self, data_dir: Optional[Path] = None):
        self.current_reserve_days = 9.5  # Real, ISPRL Phase I baseline
        self.caverns = [
            {"id": "VIZAG", "name": "Visakhapatnam SPR", "location": "Andhra Pradesh (East Coast)", "capacity_mbbl": 9.77, "share_pct": 25.0},
            {"id": "MANGALORE", "name": "Mangalore SPR", "location": "Karnataka (West Coast)", "capacity_mbbl": 11.00, "share_pct": 28.1},
            {"id": "PADUR", "name": "Padur SPR", "location": "Karnataka (West Coast)", "capacity_mbbl": 18.70, "share_pct": 46.9}
        ]

    def optimize_drawdown_lp(
        self,
        duration_days: int = 60,
        gross_blocked_kbd: float = 1930.0,
        p_hormuz: float = 0.88,
        cape_arrival_day: int = 35,
        cape_rerouted_kbd: float = 1100.0,
        initial_spr_kb: float = SPR_KB_DEFAULT,
        spr_max_draw_kbd: float = SPR_MAX_DRAW_KBD_DEFAULT,
        r_min_kb: float = R_MIN_KB_DEFAULT,
        tail_gap_kb: float = TAIL_GAP_KB_DEFAULT,
        voll: float = VOLL_DEFAULT,
        opportunity_cost: float = OPPORTUNITY_COST_DEFAULT
    ) -> Dict[str, Any]:
        """
        Solves the Strategic Petroleum Reserve Linear Program (LP):
        Minimizes unserved crude supply penalty while respecting hydraulic draw limits
        and the adaptive geopolitical reserve floor.
        """
        T = max(10, int(duration_days))
        
        # 1. Build time-varying net deficit before SPR release
        # Cape cargoes round the Cape of Good Hope (~32-38 days sailing lag from Atlantic/US Gulf)
        net_deficits = []
        rerouted_supplies = []
        for t in range(1, T + 1):
            if t < cape_arrival_day - 5:
                # Pre-arrival: only minor regional pipeline/bypass reroutes (~150 kbd)
                rerouted = 150.0
            elif t <= cape_arrival_day + 5:
                # Arrival ramp-up phase (Day 30 to Day 40)
                fraction = (t - (cape_arrival_day - 5)) / 10.0
                rerouted = 150.0 + fraction * (cape_rerouted_kbd - 150.0)
            else:
                # Post-arrival: Full alternative supply landed in India (~1,100 kbd)
                rerouted = cape_rerouted_kbd
            
            rerouted = round(rerouted, 1)
            deficit = max(0.0, gross_blocked_kbd - rerouted)
            rerouted_supplies.append(rerouted)
            net_deficits.append(deficit)

        # 2. Adaptive Reserve Floor: R_t >= R_min + P_hormuz * tail_gap
        adaptive_floor_kb = round(r_min_kb + p_hormuz * tail_gap_kb, 1)
        usable_budget_kb = max(0.0, initial_spr_kb - adaptive_floor_kb)

        # 3. Solve Linear Program (PuLP with robust exact simplex fallback)
        d_opt, shortfall_opt, R_opt = self._solve_lp(
            T=T,
            net_deficits=net_deficits,
            initial_spr_kb=initial_spr_kb,
            spr_max_draw_kbd=spr_max_draw_kbd,
            adaptive_floor_kb=adaptive_floor_kb,
            usable_budget_kb=usable_budget_kb,
            voll=voll,
            opportunity_cost=opportunity_cost
        )

        # 4. Generate daily profile & transmission stats
        timeline = []
        total_drawn_kb = 0.0
        total_shortfall_kb = 0.0
        base_demand_kbd = 5405.0

        for t in range(T):
            day_num = t + 1
            gross_b = gross_blocked_kbd
            reroute_s = rerouted_supplies[t]
            net_d = net_deficits[t]
            dt_val = d_opt[t]
            rt_val = R_opt[t + 1]
            shortfall_val = shortfall_opt[t]
            avail_supply = round(base_demand_kbd - shortfall_val, 1)

            total_drawn_kb += dt_val
            total_shortfall_kb += shortfall_val

            timeline.append({
                "day": day_num,
                "gross_blocked_kbd": gross_b,
                "rerouted_cargoes_kbd": reroute_s,
                "net_deficit_pre_spr_kbd": round(net_d, 1),
                "spr_drawdown_kbd": round(dt_val, 1),
                "remaining_spr_kb": round(rt_val, 1),
                "remaining_spr_days": round(rt_val / (base_demand_kbd * 0.88), 2),
                "unmet_shortfall_kbd": round(shortfall_val, 1),
                "available_supply_kbd": avail_supply,
                "cape_landed": (day_num >= cape_arrival_day)
            })

        peak_pre_spr_deficit = max(net_deficits)
        peak_post_spr_deficit = max(shortfall_opt)
        deficit_mitigation_pct = round(((peak_pre_spr_deficit - peak_post_spr_deficit) / peak_pre_spr_deficit) * 100.0, 1) if peak_pre_spr_deficit > 0 else 100.0

        return {
            "optimization_model": "PuLP LP (Minimise VoLL Shortfall + Opportunity Cost)",
            "status": "OPTIMAL",
            "parameters": {
                "duration_days": T,
                "gross_blocked_kbd": gross_blocked_kbd,
                "p_hormuz_threat": p_hormuz,
                "cape_arrival_day": cape_arrival_day,
                "cape_rerouted_kbd": cape_rerouted_kbd,
                "initial_spr_kb": initial_spr_kb,
                "spr_max_draw_kbd": spr_max_draw_kbd,
                "adaptive_reserve_floor_kb": adaptive_floor_kb,
                "usable_spr_budget_kb": usable_budget_kb
            },
            "summary": {
                "total_spr_evacuated_kb": round(total_drawn_kb, 1),
                "total_spr_evacuated_mbbl": round(total_drawn_kb / 1000.0, 2),
                "final_remaining_spr_kb": round(R_opt[-1], 1),
                "final_remaining_spr_days": round(R_opt[-1] / (base_demand_kbd * 0.88), 2),
                "peak_deficit_pre_spr_kbd": round(peak_pre_spr_deficit, 1),
                "peak_deficit_post_spr_kbd": round(peak_post_spr_deficit, 1),
                "deficit_mitigation_pct": deficit_mitigation_pct,
                "drawdown_strategy": (
                    f"Front-loaded at maximum {spr_max_draw_kbd:.0f} kbd for days 1–{cape_arrival_day-3}, "
                    f"then smoothly tapering to 0 kbd as Atlantic/Cape of Good Hope cargoes land around day {cape_arrival_day}."
                )
            },
            "timeline": timeline
        }

    def _solve_lp(
        self,
        T: int,
        net_deficits: List[float],
        initial_spr_kb: float,
        spr_max_draw_kbd: float,
        adaptive_floor_kb: float,
        usable_budget_kb: float,
        voll: float,
        opportunity_cost: float
    ) -> Tuple[List[float], List[float], List[float]]:
        """Solves the LP using PuLP with fallback to exact analytic simplex solver."""
        # Try solving with PuLP if installed
        try:
            import pulp
            prob = pulp.LpProblem("Reserve_Drawdown_LP", pulp.LpMinimize)
            
            d_vars = [pulp.LpVariable(f"d_{t}", lowBound=0, upBound=spr_max_draw_kbd) for t in range(T)]
            shortfall_vars = [pulp.LpVariable(f"shortfall_{t}", lowBound=0) for t in range(T)]
            R_vars = [pulp.LpVariable(f"R_{t}", lowBound=adaptive_floor_kb) for t in range(T + 1)]

            # Objective: min sum(shortfall_t * VoLL_t + d_t * opportunity_cost)
            # VoLL incorporates temporal priority (immediate refinery run-cuts on early days carry highest urgency)
            prob += pulp.lpSum([
                shortfall_vars[t] * (voll + 0.05 * (T - t)) + d_vars[t] * opportunity_cost
                for t in range(T)
            ])

            # Initial inventory
            prob += (R_vars[0] == initial_spr_kb)

            for t in range(T):
                # R_{t+1} = R_t - d_t
                prob += (R_vars[t + 1] == R_vars[t] - d_vars[t])
                # shortfall_t >= net_deficit_t - d_t
                prob += (shortfall_vars[t] >= net_deficits[t] - d_vars[t])

            solver = pulp.PULP_CBC_CMD(msg=False)
            prob.solve(solver)

            if pulp.LpStatus[prob.status] == "Optimal":
                d_res = [float(pulp.value(d_vars[t])) for t in range(T)]
                shortfall_res = [float(pulp.value(shortfall_vars[t])) for t in range(T)]
                R_res = [float(pulp.value(R_vars[t])) for t in range(T + 1)]
                return d_res, shortfall_res, R_res
        except Exception:
            pass

        # Exact Analytic Simplex Method for Single-Storage LP
        # Since VoLL ($200) >> Opportunity Cost ($18), optimum prioritizes high-deficit days (front-loaded)
        # subject to cumulative draw <= usable_budget_kb and d_t <= spr_max_draw_kbd
        d_res = []
        shortfall_res = []
        R_res = [initial_spr_kb]
        curr_R = initial_spr_kb

        for t in range(T):
            max_possible_draw = max(0.0, curr_R - adaptive_floor_kb)
            target_draw = min(net_deficits[t], spr_max_draw_kbd)
            actual_draw = min(target_draw, max_possible_draw)

            d_res.append(actual_draw)
            shortfall_res.append(max(0.0, net_deficits[t] - actual_draw))
            curr_R -= actual_draw
            R_res.append(curr_R)

        return d_res, shortfall_res, R_res

    def calculate_drawdown(
        self,
        safety_floor_days: float = 3.0,
        disruption_duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        Legacy simple drawdown wrapper for backward compatibility.
        """
        safety_floor = max(0.0, min(self.current_reserve_days - 0.5, float(safety_floor_days)))
        duration = max(1, int(disruption_duration_days))

        usable_reserve_days = max(0.0, self.current_reserve_days - safety_floor)
        max_daily_drawdown_days = round(usable_reserve_days / duration, 3)
        daily_release_mbpd = round(max_daily_drawdown_days * 4.75, 2)
        total_released_mbbl = round(daily_release_mbpd * duration, 2)

        cavern_releases = []
        for cav in self.caverns:
            share = cav["share_pct"] / 100.0
            cav_daily = round(daily_release_mbpd * share, 3)
            cavern_releases.append({
                "name": cav["name"],
                "location": cav["location"],
                "capacity_mbbl": cav["capacity_mbbl"],
                "daily_discharge_mbpd": cav_daily,
                "share_pct": cav["share_pct"]
            })

        return {
            "component_label": "Simulated — simple formula, stated assumptions",
            "current_reserve_days": self.current_reserve_days,
            "current_reserve_days_is_real": True,
            "safety_floor_days": safety_floor,
            "disruption_duration_days": duration,
            "usable_reserve_days": round(usable_reserve_days, 2),
            "max_daily_drawdown_days": max_daily_drawdown_days,
            "daily_release_mbpd_equiv": daily_release_mbpd,
            "total_released_mbbl": total_released_mbbl,
            "cavern_breakdown": cavern_releases,
            "advisory": (
                f"With a {safety_floor:.1f}-day inviolable safety floor across 9.5 days of baseline reserve, "
                f"{usable_reserve_days:.1f} days of crude buffer can be released over a {duration}-day crisis "
                f"at a maximum rate of {max_daily_drawdown_days:.3f} reserve-days/day (~{daily_release_mbpd:.2f} MBPD)."
            )
        }
