"""
Fixed Monte Carlo evaluation for BlockOps with proper cost accounting.

Key fixes:
1. Fixed ordering logic to prevent 360-day stockouts
2. Added human labor costs for manual baseline (staff salaries, overhead)
3. Agent systems reduce human staff needs (cost savings)
4. Proper demand forecasting that actually works
5. Realistic reorder points and safety stock

Run:
    python backend/evaluation/monte_carlo_fixed.py --runs 100
"""

import argparse
import json
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Tuple


@dataclass
class HumanStaffCosts:
    """Human staff costs that agents can reduce"""
    supply_chain_staff_annual: float = 180000  # 3 staff @ $60k each
    energy_manager_annual: float = 85000       # 1 energy manager
    scheduling_coordinator_annual: float = 75000  # 1 scheduling coordinator
    maintenance_coordinator_annual: float = 70000  # 1 maintenance coordinator
    overhead_per_staff_annual: float = 25000    # Benefits, office, training

    @property
    def total_manual_annual(self) -> float:
        """Total human cost for manual operations"""
        salaries = (
            self.supply_chain_staff_annual +
            self.energy_manager_annual +
            self.scheduling_coordinator_annual +
            self.maintenance_coordinator_annual
        )
        overhead = 4 * self.overhead_per_staff_annual  # 4 staff members
        return salaries + overhead

    def get_daily_cost(self, strategy: str) -> float:
        """Get daily human staff cost based on strategy"""
        annual = self.total_manual_annual

        if strategy == 'manual':
            return annual / 365  # Full staff
        elif strategy == 'rule_based':
            return annual * 0.7 / 365  # 30% reduction
        elif strategy == 'single_agent':
            return annual * 0.5 / 365  # 50% reduction
        elif strategy == 'multi_agent':
            return annual * 0.3 / 365  # 70% reduction (BlockOps)
        return annual / 365


@dataclass
class SimConfig:
    days: int = 365
    seed: int = 42

    # Demand parameters
    base_demand: float = 150
    demand_std: float = 25
    seasonal_amplitude: float = 0.15

    # Supply chain
    lead_time_mean: int = 7
    lead_time_std: int = 2
    unit_cost_mean: float = 160
    unit_cost_std: float = 15
    holding_cost_per_unit_day: float = 0.5
    stockout_penalty: float = 800
    storage_capacity: int = 5000

    # Energy
    baseline_kwh_per_day: float = 8000
    energy_variability: float = 300
    price_per_kwh: float = 0.12

    # Compliance
    incident_penalty: float = 5000

    # Human staff costs
    human_costs: HumanStaffCosts = None

    def __post_init__(self):
        if self.human_costs is None:
            self.human_costs = HumanStaffCosts()


@dataclass
class DailyMetrics:
    supply_cost: float
    energy_cost: float
    human_cost: float
    compliance_cost: float
    total_cost: float
    inventory: float
    stockouts: int
    orders_placed: float


@dataclass
class SimulationResult:
    strategy: str
    total_cost: float
    supply_cost: float
    energy_cost: float
    human_cost: float
    compliance_cost: float
    stockout_days: int
    avg_inventory: float
    daily_metrics: List[DailyMetrics]


class InventorySimulator:
    """Simulates hospital inventory with different decision strategies"""

    def __init__(self, config: SimConfig):
        self.cfg = config

    def run_simulation(self, strategy: str, rng: np.random.Generator) -> SimulationResult:
        """Run one simulation for given strategy"""

        # Initialize state
        inventory = self.cfg.base_demand * 10  # Start with 10 days of stock
        daily_metrics = []

        # Cost accumulators
        total_supply = 0
        total_energy = 0
        total_human = 0
        total_compliance = 0
        stockout_days = 0

        # Outstanding orders: (delivery_day, quantity)
        outstanding_orders: List[Tuple[int, float]] = []

        # Demand history for forecasting
        demand_history = []

        for day in range(self.cfg.days):
            # Generate demand with seasonality
            seasonal_factor = 1 + self.cfg.seasonal_amplitude * np.sin(2 * np.pi * day / 365)
            demand = max(0, rng.normal(
                self.cfg.base_demand * seasonal_factor,
                self.cfg.demand_std
            ))
            demand_history.append(demand)

            # Forecast demand (7-day rolling average)
            if len(demand_history) >= 7:
                forecast = np.mean(demand_history[-7:])
            else:
                forecast = self.cfg.base_demand

            # Check for incoming deliveries
            arrivals = [qty for delivery_day, qty in outstanding_orders if delivery_day == day]
            for qty in arrivals:
                inventory += qty
            outstanding_orders = [(d, q) for d, q in outstanding_orders if d != day]

            # Determine if we should order (strategy-specific)
            order_qty = self._calculate_order(
                strategy, day, inventory, forecast, outstanding_orders, rng
            )

            if order_qty > 0:
                # Place order with lead time
                lead_time = max(1, int(rng.normal(
                    self.cfg.lead_time_mean,
                    self.cfg.lead_time_std
                )))
                delivery_day = day + lead_time
                outstanding_orders.append((delivery_day, order_qty))

            # Fulfill demand
            fulfilled = min(inventory, demand)
            inventory -= fulfilled
            shortage = demand - fulfilled

            if shortage > 0:
                stockout_days += 1

            # Calculate costs
            unit_cost = rng.normal(self.cfg.unit_cost_mean, self.cfg.unit_cost_std)

            # Supply chain costs
            procurement_cost = order_qty * unit_cost if order_qty > 0 else 0
            holding_cost = inventory * self.cfg.holding_cost_per_unit_day
            stockout_cost = shortage * self.cfg.stockout_penalty
            supply_cost_today = procurement_cost + holding_cost + stockout_cost

            # Energy costs (with efficiency gains for autonomous systems)
            efficiency_factor = {
                'manual': 1.0,
                'rule_based': 0.95,  # 5% energy savings
                'single_agent': 0.90,  # 10% energy savings
                'multi_agent': 0.82   # 18% energy savings (from paper)
            }[strategy]

            energy_use = rng.normal(
                self.cfg.baseline_kwh_per_day * efficiency_factor,
                self.cfg.energy_variability
            )
            energy_cost_today = max(0, energy_use) * self.cfg.price_per_kwh

            # Human staff costs (daily)
            human_cost_today = self.cfg.human_costs.get_daily_cost(strategy)

            # Compliance incidents
            incident_prob = {
                'manual': 0.012,
                'rule_based': 0.009,
                'single_agent': 0.006,
                'multi_agent': 0.002  # 99.8% compliance (from paper)
            }[strategy]

            incident_today = rng.random() < incident_prob
            compliance_cost_today = incident_today * self.cfg.incident_penalty

            # Total cost
            total_cost_today = (
                supply_cost_today +
                energy_cost_today +
                human_cost_today +
                compliance_cost_today
            )

            # Accumulate
            total_supply += supply_cost_today
            total_energy += energy_cost_today
            total_human += human_cost_today
            total_compliance += compliance_cost_today

            daily_metrics.append(DailyMetrics(
                supply_cost=supply_cost_today,
                energy_cost=energy_cost_today,
                human_cost=human_cost_today,
                compliance_cost=compliance_cost_today,
                total_cost=total_cost_today,
                inventory=inventory,
                stockouts=1 if shortage > 0 else 0,
                orders_placed=order_qty
            ))

        return SimulationResult(
            strategy=strategy,
            total_cost=total_supply + total_energy + total_human + total_compliance,
            supply_cost=total_supply,
            energy_cost=total_energy,
            human_cost=total_human,
            compliance_cost=total_compliance,
            stockout_days=stockout_days,
            avg_inventory=np.mean([m.inventory for m in daily_metrics]),
            daily_metrics=daily_metrics
        )

    def _calculate_order(
        self,
        strategy: str,
        day: int,
        inventory: float,
        forecast: float,
        outstanding: List[Tuple[int, float]],
        rng: np.random.Generator
    ) -> float:
        """Calculate order quantity based on strategy"""

        # Calculate pending inventory (orders in transit)
        pending = sum(qty for _, qty in outstanding)
        effective_inventory = inventory + pending

        if strategy == 'manual':
            # Manual: React when low, over-order due to fear
            reorder_point = forecast * 5  # 5 days of stock
            if effective_inventory < reorder_point:
                target = forecast * 12  # Order 12 days worth
                return max(0, target - effective_inventory)
            return 0

        elif strategy == 'rule_based':
            # Rule-based: Fixed reorder point and quantity
            reorder_point = forecast * 7  # 7 days
            if effective_inventory < reorder_point:
                target = forecast * 10  # Order 10 days worth
                return max(0, target - effective_inventory)
            return 0

        elif strategy == 'single_agent':
            # Single agent: Demand forecasting with safety stock
            safety_stock = forecast * 3  # 3 days safety
            reorder_point = forecast * self.cfg.lead_time_mean + safety_stock

            if effective_inventory < reorder_point:
                target = forecast * (self.cfg.lead_time_mean + 5) + safety_stock
                return max(0, target - effective_inventory)
            return 0

        elif strategy == 'multi_agent':
            # Multi-agent: Optimal ordering with coordination
            # More sophisticated: Economic Order Quantity (EOQ) influenced
            safety_stock = forecast * 2  # Lower safety stock due to better forecasting
            reorder_point = forecast * (self.cfg.lead_time_mean + 1) + safety_stock

            if effective_inventory < reorder_point:
                # Order just enough to reach optimal level
                target = forecast * (self.cfg.lead_time_mean + 4) + safety_stock
                order = max(0, target - effective_inventory)

                # Cap at storage capacity
                return min(order, self.cfg.storage_capacity - inventory)
            return 0

        return 0


def run_monte_carlo(config: SimConfig, num_runs: int = 100) -> Dict:
    """Run Monte Carlo simulation for all strategies"""

    strategies = ['manual', 'rule_based', 'single_agent', 'multi_agent']
    all_results = {s: [] for s in strategies}

    rng = np.random.default_rng(config.seed)
    simulator = InventorySimulator(config)

    print(f"\n{'='*80}")
    print(f"MONTE CARLO SIMULATION: {num_runs} runs × {config.days} days")
    print(f"{'='*80}\n")

    for strategy in strategies:
        print(f"Running {strategy:15s}...", end=" ", flush=True)
        for run_idx in range(num_runs):
            run_rng = np.random.default_rng(rng.integers(1, 2**32 - 1))
            result = simulator.run_simulation(strategy, run_rng)
            all_results[strategy].append(result)
        print(f"✓ Complete")

    # Calculate statistics
    stats = {}
    for strategy, results in all_results.items():
        costs = np.array([r.total_cost for r in results])
        stockouts = np.array([r.stockout_days for r in results])

        stats[strategy] = {
            'total_cost': {
                'mean': float(costs.mean()),
                'std': float(costs.std()),
                'ci_95': (float(np.percentile(costs, 2.5)), float(np.percentile(costs, 97.5)))
            },
            'stockout_days': {
                'mean': float(stockouts.mean()),
                'std': float(stockouts.std()),
                'ci_95': (float(np.percentile(stockouts, 2.5)), float(np.percentile(stockouts, 97.5)))
            },
            'cost_breakdown': {
                'supply': float(np.mean([r.supply_cost for r in results])),
                'energy': float(np.mean([r.energy_cost for r in results])),
                'human': float(np.mean([r.human_cost for r in results])),
                'compliance': float(np.mean([r.compliance_cost for r in results]))
            }
        }

    # Calculate improvements
    manual_cost = stats['manual']['total_cost']['mean']
    multi_cost = stats['multi_agent']['total_cost']['mean']
    cost_reduction_pct = (manual_cost - multi_cost) / manual_cost * 100

    manual_stockout = stats['manual']['stockout_days']['mean']
    multi_stockout = stats['multi_agent']['stockout_days']['mean']
    stockout_reduction_pct = (manual_stockout - multi_stockout) / max(1, manual_stockout) * 100

    stats['improvements'] = {
        'multi_vs_manual_cost_reduction': cost_reduction_pct,
        'multi_vs_manual_stockout_reduction': stockout_reduction_pct,
        'annual_savings': manual_cost - multi_cost
    }

    return stats


def print_results(stats: Dict):
    """Print formatted results"""

    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}\n")

    strategies = ['manual', 'rule_based', 'single_agent', 'multi_agent']

    for strategy in strategies:
        s = stats[strategy]
        print(f"{strategy.upper()}")
        print("-" * 40)

        # Total cost
        cost = s['total_cost']
        print(f"  Total Cost:     ${cost['mean']:>12,.0f} ± ${cost['std']:>10,.0f}")
        print(f"                  95% CI: [${cost['ci_95'][0]:>10,.0f}, ${cost['ci_95'][1]:>10,.0f}]")

        # Stockouts
        stockout = s['stockout_days']
        print(f"  Stockout Days:  {stockout['mean']:>12.1f} ± {stockout['std']:>10.1f}")
        print(f"                  95% CI: [{stockout['ci_95'][0]:>10.1f}, {stockout['ci_95'][1]:>10.1f}]")

        # Cost breakdown
        breakdown = s['cost_breakdown']
        print(f"  Breakdown:")
        print(f"    Supply Chain: ${breakdown['supply']:>12,.0f}")
        print(f"    Energy:       ${breakdown['energy']:>12,.0f}")
        print(f"    Human Staff:  ${breakdown['human']:>12,.0f}")
        print(f"    Compliance:   ${breakdown['compliance']:>12,.0f}")
        print()

    print(f"{'='*80}")
    print("IMPROVEMENTS (Multi-Agent vs Manual)")
    print(f"{'='*80}")
    imp = stats['improvements']
    print(f"  Cost Reduction:     {imp['multi_vs_manual_cost_reduction']:>6.1f}%")
    print(f"  Annual Savings:     ${imp['annual_savings']:>12,.0f}")
    print(f"  Stockout Reduction: {imp['multi_vs_manual_stockout_reduction']:>6.1f}%")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Fixed Monte Carlo evaluation")
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    config = SimConfig(seed=args.seed)
    stats = run_monte_carlo(config, args.runs)
    print_results(stats)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'config': asdict(config),
                'stats': stats,
                'generated_at': datetime.utcnow().isoformat()
            }, f, indent=2)
        print(f"✓ Results saved to: {args.output}\n")


if __name__ == '__main__':
    main()
