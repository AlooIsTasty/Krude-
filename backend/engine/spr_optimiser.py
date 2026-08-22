"""
Krude - Component 4: Strategic Reserve Optimisation Agent (SIMULATED)
=====================================================================
Formula:
max_daily_drawdown_days = (current_reserve_days - safety_floor_days) / disruption_duration_days

- current_reserve_days = 9.5 (real, from public data).
- safety_floor_days and disruption_duration_days are assumptions ("simulated data").
"""

from typing import Dict, Any

class StrategicReserveOptimiser:
    """
    Component 4: Strategic Reserve Optimisation Agent (SIMULATED)
    Models calibrated SPR cavern drawdown against physical reserve days.
    """
    def __init__(self):
        self.current_reserve_days = 9.5  # Real, from public data
        self.caverns = [
            {"id": "VIZAG", "name": "Visakhapatnam SPR", "location": "Andhra Pradesh (East Coast)", "capacity_mbbl": 9.77, "share_pct": 25.0},
            {"id": "MANGALORE", "name": "Mangalore SPR", "location": "Karnataka (West Coast)", "capacity_mbbl": 11.00, "share_pct": 28.1},
            {"id": "PADUR", "name": "Padur SPR", "location": "Karnataka (West Coast)", "capacity_mbbl": 18.33, "share_pct": 46.9}
        ]

    def calculate_drawdown(
        self,
        safety_floor_days: float = 3.0,
        disruption_duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculates daily reserve release rate based on the exact formula:
        max_daily_drawdown_days = (current_reserve_days - safety_floor_days) / disruption_duration_days
        """
        safety_floor = max(0.0, min(self.current_reserve_days - 0.5, float(safety_floor_days)))
        duration = max(1, int(disruption_duration_days))

        # Usable reserve buffer
        usable_reserve_days = max(0.0, self.current_reserve_days - safety_floor)
        
        # Exact formula:
        # max_daily_drawdown_days = (current_reserve_days - safety_floor_days) / disruption_duration_days
        max_daily_drawdown_days = round(usable_reserve_days / duration, 3)

        # In million barrels per day equivalent (assuming India ~4.75 MBPD import demand)
        daily_release_mbpd = round(max_daily_drawdown_days * 4.75, 2)
        total_released_mbbl = round(daily_release_mbpd * duration, 2)

        # Breakdown across the 3 public SPR caverns
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
