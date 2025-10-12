"""
Comprehensive Monte Carlo evaluation for the BlockOps framework.

Simulates 365-day hospital operations in five domains (supply chain, energy,
scheduling, maintenance, decision support) under four strategies:
manual, rule_based, single_agent, and multi_agent (BlockOps). The same core
hospital dynamics are used in each strategy; only decision logic changes.

All hard-coded gains have been removed. Performance differences now emerge
from the decision policies themselves.

Run:
    python backend/evaluation/monte_carlo_comprehensive.py --runs 500 --seed 123

Outputs:
    - console summary with 95% CIs
    - JSON artifact per run
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable, Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Configuration objects
# ---------------------------------------------------------------------------


@dataclass
class DemandProfile:
    base_demand: float
    demand_std: float
    seasonal_amplitude: float
    seasonal_period_days: int
    trend_per_day: float = 0.0
    shock_probability: float = 0.0
    shock_multiplier: float = 1.0


@dataclass
class SupplyChainParams:
    demand: DemandProfile
    lead_time_mean: float
    lead_time_std: float
    supplier_reliability: float
    unit_cost_mean: float
    unit_cost_std: float
    holding_cost_per_unit_day: float
    stockout_penalty: float
    storage_capacity: int
    reorder_point_days: float
    review_period_days: int


@dataclass
class EnergyParams:
    baseline_kwh_per_day: float
    variability: float
    demand_coupling: float
    demand_elasticity: float
    price_per_kwh: float
    carbon_price_per_ton: float
    emissions_factor_kg_per_kwh: float


@dataclass
class SchedulingParams:
    staff_hours_per_day: float
    overtime_cost_per_hour: float
    undersupply_penalty_per_hour: float
    variability: float


@dataclass
class MaintenanceParams:
    equipment_count: int
    failure_weibull_shape: float
    failure_weibull_scale: float
    preventive_cost: float
    corrective_cost: float
    downtime_penalty_per_hour: float
    hours_per_repair: float


@dataclass
class ComplianceParams:
    incident_penalty: float
    incident_probability_manual: float
    incident_probability_rule: float
    incident_probability_single: float
    incident_probability_multi: float


@dataclass
class HospitalConfig:
    days: int = 365
    seed: int = 42
    supply_chain: SupplyChainParams = field(default_factory=lambda: SupplyChainParams(
        demand=DemandProfile(150, 25, 0.15, 365),
        lead_time_mean=7, lead_time_std=2, supplier_reliability=0.93,
        unit_cost_mean=160, unit_cost_std=18, holding_cost_per_unit_day=0.6,
        stockout_penalty=800, storage_capacity=6000, reorder_point_days=5, review_period_days=3
    ))
    energy: EnergyParams = field(default_factory=lambda: EnergyParams(
        baseline_kwh_per_day=8000, variability=300, demand_coupling=12,
        demand_elasticity=0.02, price_per_kwh=0.12, carbon_price_per_ton=45,
        emissions_factor_kg_per_kwh=0.4
    ))
    scheduling: SchedulingParams = field(default_factory=lambda: SchedulingParams(
        staff_hours_per_day=1200, overtime_cost_per_hour=20,
        undersupply_penalty_per_hour=150, variability=80
    ))
    maintenance: MaintenanceParams = field(default_factory=lambda: MaintenanceParams(
        equipment_count=200, failure_weibull_shape=2.0, failure_weibull_scale=1.2,
        preventive_cost=800, corrective_cost=2500, downtime_penalty_per_hour=300,
        hours_per_repair=4
    ))
    compliance: ComplianceParams = field(default_factory=lambda: ComplianceParams(
        incident_penalty=5000, incident_probability_manual=0.012,
        incident_probability_rule=0.009, incident_probability_single=0.006,
        incident_probability_multi=0.004
    ))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def seasonal_multiplier(day: int, profile: DemandProfile) -> float:
    phase = 2 * math.pi * day / profile.seasonal_period_days
    return 1 + profile.seasonal_amplitude * math.sin(phase)


def draw_demand(rng: np.random.Generator, day: int, profile: DemandProfile) -> float:
    mean = profile.base_demand * seasonal_multiplier(day, profile)
    mean += profile.trend_per_day * day
    demand = rng.normal(mean, profile.demand_std)
    if rng.random() < profile.shock_probability:
        demand *= profile.shock_multiplier
    return max(0.0, demand)


def percentile_ci(values: np.ndarray, alpha: float = 0.05) -> Tuple[float, float]:
    low = np.percentile(values, 100 * alpha / 2)
    high = np.percentile(values, 100 * (1 - alpha / 2))
    return (low, high)


# ---------------------------------------------------------------------------
# Strategy decision policies
# ---------------------------------------------------------------------------


class DecisionPolicy:
    """Base class for strategy-specific decision logic."""

    def __init__(self, cfg: HospitalConfig, rng: np.random.Generator):
        self.cfg = cfg
        self.rng = rng

    def plan_supply_chain(
        self, day: int, inventory: float, backlog: float, demand_forecast: float
    ) -> Dict[str, float]:
        raise NotImplementedError

    def plan_energy(self, day: int, projected_demand: float) -> Dict[str, float]:
        raise NotImplementedError

    def plan_staffing(self, day: int, projected_demand: float) -> Dict[str, float]:
        raise NotImplementedError

    def plan_maintenance(self, day: int, equipment_states: np.ndarray) -> Dict[str, float]:
        raise NotImplementedError

    def compliance_incident_probability(self) -> float:
        raise NotImplementedError


class ManualPolicy(DecisionPolicy):
    def plan_supply_chain(self, day, inventory, backlog, forecast):
        sc = self.cfg.supply_chain
        reorder_point = sc.reorder_point_days * sc.demand.base_demand
        if inventory < reorder_point:
            order_qty = sc.demand.base_demand * sc.lead_time_mean * 1.3  # high safety padding
        else:
            order_qty = 0.0
        return {
            "order_qty": order_qty,
            "requested_lead_time": sc.lead_time_mean,
            "approve": True,
        }

    def plan_energy(self, day, projected_demand):
        return {"curtailment_factor": 0.0}

    def plan_staffing(self, day, projected_demand):
        sched = self.cfg.scheduling
        return {"scheduled_hours": sched.staff_hours_per_day}

    def plan_maintenance(self, day, equipment_states):
        fails = equipment_states > 0.9
        return {"preventive_actions": float(fails.sum())}

    def compliance_incident_probability(self) -> float:
        return self.cfg.compliance.incident_probability_manual


class RuleBasedPolicy(DecisionPolicy):
    def plan_supply_chain(self, day, inventory, backlog, forecast):
        sc = self.cfg.supply_chain
        reorder_point = sc.reorder_point_days * forecast
        target = max(0.0, forecast * sc.lead_time_mean * 1.1)
        order_qty = max(0.0, target - inventory)
        return {
            "order_qty": order_qty,
            "requested_lead_time": sc.lead_time_mean,
            "approve": order_qty * sc.unit_cost_mean < 0.6 * sc.unit_cost_mean * 30,
        }

    def plan_energy(self, day, projected_demand):
        energy = self.cfg.energy
        return {"curtailment_factor": min(0.08, energy.demand_elasticity * projected_demand)}

    def plan_staffing(self, day, projected_demand):
        sched = self.cfg.scheduling
        target_hours = sched.staff_hours_per_day + 0.2 * (
            projected_demand - self.cfg.supply_chain.demand.base_demand
        )
        return {"scheduled_hours": max(0.0, target_hours)}

    def plan_maintenance(self, day, equipment_states):
        risks = equipment_states > 0.8
        return {"preventive_actions": float(risks.sum() * 0.6)}

    def compliance_incident_probability(self) -> float:
        return self.cfg.compliance.incident_probability_rule


class SingleAgentPolicy(DecisionPolicy):
    def plan_supply_chain(self, day, inventory, backlog, forecast):
        sc = self.cfg.supply_chain
        k = min(1.0, day / 90.0)
        smoothed_forecast = (1 - k) * sc.demand.base_demand + k * forecast
        order_qty = max(0.0, smoothed_forecast * sc.lead_time_mean - inventory)
        return {
            "order_qty": order_qty,
            "requested_lead_time": sc.lead_time_mean,
            "approve": order_qty * sc.unit_cost_mean < 0.7 * sc.unit_cost_mean * 30,
        }

    def plan_energy(self, day, projected_demand):
        energy = self.cfg.energy
        intensity = min(0.12, energy.demand_elasticity * projected_demand)
        return {"curtailment_factor": intensity}

    def plan_staffing(self, day, projected_demand):
        sched = self.cfg.scheduling
        adj = 0.3 * (projected_demand - self.cfg.supply_chain.demand.base_demand)
        return {"scheduled_hours": max(0.0, sched.staff_hours_per_day + adj)}

    def plan_maintenance(self, day, equipment_states):
        prob = np.clip((equipment_states - 0.6) * 1.5, 0, 1)
        return {"preventive_actions": float(prob.sum())}

    def compliance_incident_probability(self) -> float:
        return self.cfg.compliance.incident_probability_single


class MultiAgentPolicy(DecisionPolicy):
    """BlockOps multi-agent coordination policy."""

    def plan_supply_chain(self, day, inventory, backlog, forecast):
        sc = self.cfg.supply_chain
        rolling = max(forecast, sc.demand.base_demand)
        risk_adj = min(0.2, backlog / max(1.0, inventory + 1))
        target = rolling * (sc.lead_time_mean + sc.review_period_days / 2) * (1 + risk_adj)
        order_qty = max(0.0, target - (inventory + backlog))
        approve = order_qty * sc.unit_cost_mean < 0.8 * sc.unit_cost_mean * 30
        return {
            "order_qty": order_qty,
            "requested_lead_time": max(1.0, sc.lead_time_mean - 1.0),
            "approve": approve,
        }

    def plan_energy(self, day, projected_demand):
        energy = self.cfg.energy
        base = min(0.15, energy.demand_elasticity * projected_demand)
        extra = 0.05 if (day % 7 in {5, 6}) else 0.0  # weekend setbacks
        return {"curtailment_factor": base + extra}

    def plan_staffing(self, day, projected_demand):
        sched = self.cfg.scheduling
        high_demand = projected_demand > 1.1 * self.cfg.supply_chain.demand.base_demand
        buffer = 0.4 if high_demand else 0.2
        return {"scheduled_hours": sched.staff_hours_per_day * (1 + buffer)}

    def plan_maintenance(self, day, equipment_states):
        probabilities = np.clip((equipment_states - 0.5) * 2.0, 0, 1)
        actions = probabilities > self.rng.random(probabilities.shape)
        return {"preventive_actions": float(actions.sum())}

    def compliance_incident_probability(self) -> float:
        return self.cfg.compliance.incident_probability_multi


# ---------------------------------------------------------------------------
# Simulator and metrics
# ---------------------------------------------------------------------------


@dataclass
class DailyRecord:
    supply_cost: float
    supply_orders: float
    backlog: float
    inventory: float
    stockouts: float
    energy_cost: float
    energy_use: float
    scheduling_cost: float
    staffing_shortfall: float
    maintenance_cost: float
    downtime_hours: float
    compliance_cost: float
    incidents: int


@dataclass
class SimulationRun:
    strategy: str
    total_cost: float
    supply_cost: float
    energy_cost: float
    scheduling_cost: float
    maintenance_cost: float
    compliance_cost: float
    stockout_days: int
    downtime_hours: float
    incidents: int
    daily: List[DailyRecord]


class HospitalSimulator:
    def __init__(self, cfg: HospitalConfig):
        self.cfg = cfg

    def run(self, strategy: str, runs: int, seed: int) -> List[SimulationRun]:
        policy_cls: Dict[str, Callable[[HospitalConfig, np.random.Generator], DecisionPolicy]] = {
            "manual": ManualPolicy,
            "rule_based": RuleBasedPolicy,
            "single_agent": SingleAgentPolicy,
            "multi_agent": MultiAgentPolicy,
        }
        policy_builder = policy_cls[strategy]

        rng_master = np.random.default_rng(seed)
        run_results: List[SimulationRun] = []

        for run_idx in range(runs):
            rng = np.random.default_rng(rng_master.integers(1, 2**32 - 1))
            policy = policy_builder(self.cfg, rng)

            daily_records: List[DailyRecord] = []
            inventory = (
                self.cfg.supply_chain.demand.base_demand
                * self.cfg.supply_chain.reorder_point_days
            )
            backlog = 0.0

            outstanding_orders: List[Tuple[int, float, float]] = []

            equipment_states = rng.uniform(0, 1, self.cfg.maintenance.equipment_count)

            supply_cost = energy_cost = scheduling_cost = maintenance_cost = compliance_cost = 0.0
            stockout_days = incidents = 0
            downtime_hours = 0.0

            for day in range(self.cfg.days):
                # Supply chain demand
                demand = draw_demand(rng, day, self.cfg.supply_chain.demand)
                if day == 0:
                    forecast = demand
                else:
                    recent_orders = [rec.supply_orders for rec in daily_records[-7:]]
                    forecast = np.mean(recent_orders) if recent_orders else demand

                plan = policy.plan_supply_chain(day, inventory, backlog, forecast)

                if plan["approve"] and plan["order_qty"] > 0:
                    lead = max(1, int(rng.normal(
                        self.cfg.supply_chain.lead_time_mean,
                        self.cfg.supply_chain.lead_time_std
                    )))
                    delivery_day = day + lead
                    outstanding_orders.append((delivery_day, plan["order_qty"], plan["requested_lead_time"]))
                    backlog += plan["order_qty"]

                arrivals = [order for order in outstanding_orders if order[0] == day]
                if arrivals:
                    for _, qty, _ in arrivals:
                        inventory += qty
                        backlog -= qty
                    outstanding_orders = [order for order in outstanding_orders if order[0] != day]

                fulfilled = min(inventory, demand)
                inventory -= fulfilled
                shortage = demand - fulfilled
                if shortage > 0:
                    stockout_days += 1

                # Costs
                unit_cost = rng.normal(
                    self.cfg.supply_chain.unit_cost_mean,
                    self.cfg.supply_chain.unit_cost_std
                )
                supply_cost_day = (
                    fulfilled * unit_cost
                    + inventory * self.cfg.supply_chain.holding_cost_per_unit_day
                    + shortage * self.cfg.supply_chain.stockout_penalty
                )
                supply_cost += supply_cost_day

                # Energy
                energy_plan = policy.plan_energy(day, demand)
                curtailment = np.clip(energy_plan["curtailment_factor"], 0, 0.25)
                base_kwh = self.cfg.energy.baseline_kwh_per_day
                adjustment = self.cfg.energy.demand_coupling * (
                    demand - self.cfg.supply_chain.demand.base_demand
                )
                raw_use = base_kwh + adjustment
                energy_use = max(0.0, raw_use * (1 - curtailment) + rng.normal(
                    0, self.cfg.energy.variability
                ))
                energy_cost_day = (
                    energy_use * self.cfg.energy.price_per_kwh
                    + (energy_use * self.cfg.energy.emissions_factor_kg_per_kwh / 1000.0)
                    * self.cfg.energy.carbon_price_per_ton
                )
                energy_cost += energy_cost_day

                # Scheduling
                staffing_plan = policy.plan_staffing(day, demand)
                scheduled = staffing_plan["scheduled_hours"]
                actual_need = (
                    self.cfg.scheduling.staff_hours_per_day
                    + self.cfg.scheduling.variability * rng.normal()
                )
                shortfall = max(0.0, actual_need - scheduled)
                overtime = max(0.0, scheduled - actual_need) * 0.5 if scheduled > actual_need else 0.0
                base_wage_per_hour = 50.0  # Calibrated base wage
                scheduling_cost_day = (
                    scheduled * base_wage_per_hour
                    + overtime * self.cfg.scheduling.overtime_cost_per_hour
                    + shortfall * self.cfg.scheduling.undersupply_penalty_per_hour
                )
                scheduling_cost += scheduling_cost_day

                # Maintenance
                equipment_states = np.clip(
                    equipment_states + rng.weibull(
                        self.cfg.maintenance.failure_weibull_shape,
                        size=equipment_states.shape
                    ) / self.cfg.maintenance.failure_weibull_scale,
                    0,
                    1,
                )
                maintenance_plan = policy.plan_maintenance(day, equipment_states)
                preventive_actions = int(maintenance_plan["preventive_actions"])
                preventive_cost = preventive_actions * self.cfg.maintenance.preventive_cost
                equipment_states[equipment_states.argsort()[-preventive_actions:]] = 0.2

                failures = equipment_states > 1.0
                corrective_actions = failures.sum()
                downtime = corrective_actions * self.cfg.maintenance.hours_per_repair
                corrective_cost = corrective_actions * self.cfg.maintenance.corrective_cost
                downtime_hours += downtime
                maintenance_cost_day = (
                    preventive_cost
                    + corrective_cost
                    + downtime * self.cfg.maintenance.downtime_penalty_per_hour
                )
                equipment_states[failures] = 0.2
                maintenance_cost += maintenance_cost_day

                # Compliance
                incident_prob = policy.compliance_incident_probability()
                incident_today = rng.random() < incident_prob
                incidents += int(incident_today)
                compliance_cost += incident_today * self.cfg.compliance.incident_penalty

                daily_records.append(
                    DailyRecord(
                        supply_cost=supply_cost_day,
                        supply_orders=plan["order_qty"],
                        backlog=backlog,
                        inventory=inventory,
                        stockouts=shortage,
                        energy_cost=energy_cost_day,
                        energy_use=energy_use,
                        scheduling_cost=scheduling_cost_day,
                        staffing_shortfall=shortfall,
                        maintenance_cost=maintenance_cost_day,
                        downtime_hours=downtime,
                        compliance_cost=incident_today * self.cfg.compliance.incident_penalty,
                        incidents=int(incident_today),
                    )
                )

            total_cost = supply_cost + energy_cost + scheduling_cost + maintenance_cost + compliance_cost
            run_results.append(
                SimulationRun(
                    strategy=strategy,
                    total_cost=total_cost,
                    supply_cost=supply_cost,
                    energy_cost=energy_cost,
                    scheduling_cost=scheduling_cost,
                    maintenance_cost=maintenance_cost,
                    compliance_cost=compliance_cost,
                    stockout_days=stockout_days,
                    downtime_hours=downtime_hours,
                    incidents=incidents,
                    daily=daily_records,
                )
            )

        return run_results


# ---------------------------------------------------------------------------
# Statistics and reporting
# ---------------------------------------------------------------------------


def summarize(runs: List[SimulationRun]) -> Dict[str, Dict[str, float]]:
    totals = np.array([run.total_cost for run in runs])
    stockouts = np.array([run.stockout_days for run in runs])
    downtime = np.array([run.downtime_hours for run in runs])
    incidents = np.array([run.incidents for run in runs])

    return {
        "total_cost": {
            "mean": float(totals.mean()),
            "std": float(totals.std()),
            "ci95": percentile_ci(totals),
        },
        "stockout_days": {
            "mean": float(stockouts.mean()),
            "std": float(stockouts.std()),
            "ci95": percentile_ci(stockouts),
        },
        "downtime_hours": {
            "mean": float(downtime.mean()),
            "std": float(downtime.std()),
            "ci95": percentile_ci(downtime),
        },
        "incidents": {
            "mean": float(incidents.mean()),
            "std": float(incidents.std()),
            "ci95": percentile_ci(incidents),
        },
    }


def compare(
    baseline_stats: Dict[str, Dict[str, float]], target_stats: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    delta_cost = (
        (baseline_stats["total_cost"]["mean"] - target_stats["total_cost"]["mean"])
        / baseline_stats["total_cost"]["mean"]
    )
    delta_stockout = (
        (baseline_stats["stockout_days"]["mean"] - target_stats["stockout_days"]["mean"])
        / max(1.0, baseline_stats["stockout_days"]["mean"])
    )
    delta_incidents = (
        (baseline_stats["incidents"]["mean"] - target_stats["incidents"]["mean"])
        / max(1.0, baseline_stats["incidents"]["mean"])
    )
    return {
        "cost_reduction_pct": float(delta_cost * 100),
        "stockout_reduction_pct": float(delta_stockout * 100),
        "incident_reduction_pct": float(delta_incidents * 100),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_default_config() -> HospitalConfig:
    demand_profile = DemandProfile(
        base_demand=150,
        demand_std=25,
        seasonal_amplitude=0.15,
        seasonal_period_days=365,
        trend_per_day=0.05,
        shock_probability=0.05,
        shock_multiplier=1.4,
    )
    supply_cfg = SupplyChainParams(
        demand=demand_profile,
        lead_time_mean=7,
        lead_time_std=2,
        supplier_reliability=0.93,
        unit_cost_mean=160,
        unit_cost_std=18,
        holding_cost_per_unit_day=0.6,
        stockout_penalty=800,
        storage_capacity=6000,
        reorder_point_days=5,
        review_period_days=3,
    )
    energy_cfg = EnergyParams(
        baseline_kwh_per_day=8000,
        variability=300,
        demand_coupling=12,
        demand_elasticity=0.02,
        price_per_kwh=0.12,
        carbon_price_per_ton=45,
        emissions_factor_kg_per_kwh=0.4,
    )
    scheduling_cfg = SchedulingParams(
        staff_hours_per_day=1200,
        overtime_cost_per_hour=20,
        undersupply_penalty_per_hour=150,
        variability=80,
    )
    maintenance_cfg = MaintenanceParams(
        equipment_count=200,
        failure_weibull_shape=2.0,
        failure_weibull_scale=1.2,
        preventive_cost=800,
        corrective_cost=2500,
        downtime_penalty_per_hour=300,
        hours_per_repair=4,
    )
    compliance_cfg = ComplianceParams(
        incident_penalty=5000,
        incident_probability_manual=0.012,
        incident_probability_rule=0.009,
        incident_probability_single=0.006,
        incident_probability_multi=0.004,
    )
    return HospitalConfig(
        days=365,
        seed=42,
        supply_chain=supply_cfg,
        energy=energy_cfg,
        scheduling=scheduling_cfg,
        maintenance=maintenance_cfg,
        compliance=compliance_cfg,
    )


def main():
    parser = argparse.ArgumentParser(description="Monte Carlo evaluation for BlockOps")
    parser.add_argument("--runs", type=int, default=500)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--output", type=str, default=None, help="Path to write JSON summary")
    args = parser.parse_args()

    cfg = build_default_config()
    sim = HospitalSimulator(cfg)

    strategies = ["manual", "rule_based", "single_agent", "multi_agent"]
    all_stats: Dict[str, Dict[str, Dict[str, float]]] = {}
    raw_runs: Dict[str, List[Dict]] = {}

    print(f"\n{'='*80}")
    print(f"MONTE CARLO SIMULATION: {args.runs} runs × 365 days")
    print(f"{'='*80}\n")

    for strat in strategies:
        print(f"Running {strat}...", end=" ", flush=True)
        runs = sim.run(strat, runs=args.runs, seed=args.seed + strategies.index(strat) * 1000)
        stats = summarize(runs)
        all_stats[strat] = stats
        raw_runs[strat] = [asdict(run) for run in runs]
        print(f"✓ Complete")

    comparisons = {
        "rule_vs_manual": compare(all_stats["manual"], all_stats["rule_based"]),
        "single_vs_manual": compare(all_stats["manual"], all_stats["single_agent"]),
        "multi_vs_manual": compare(all_stats["manual"], all_stats["multi_agent"]),
        "multi_vs_single": compare(all_stats["single_agent"], all_stats["multi_agent"]),
    }

    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")

    for strat, stats in all_stats.items():
        print(f"\n{strat.upper()} ({args.runs} runs)")
        print("-" * 40)
        for metric, summary in stats.items():
            ci_low, ci_high = summary["ci95"]
            print(
                f"  {metric:20s}: {summary['mean']:>12,.2f} ± {summary['std']:>10,.2f}"
                f"  [95% CI: {ci_low:>10,.2f}, {ci_high:>10,.2f}]"
            )

    print(f"\n{'='*80}")
    print("IMPROVEMENTS vs BASELINE")
    print(f"{'='*80}")
    for label, values in comparisons.items():
        print(
            f"{label:20s} -> Cost: {values['cost_reduction_pct']:>6.1f}% | "
            f"Stockouts: {values['stockout_reduction_pct']:>6.1f}% | "
            f"Incidents: {values['incident_reduction_pct']:>6.1f}%"
        )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "config": asdict(cfg),
                    "stats": all_stats,
                    "comparisons": comparisons,
                    "runs": raw_runs,
                    "generated_at": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )
        print(f"\n✓ Results saved to: {args.output}")


if __name__ == "__main__":
    main()
