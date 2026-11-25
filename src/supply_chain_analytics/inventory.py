"""Small inventory-planning calculations using consistent time and value units."""

import math
from numbers import Real


def _nonnegative(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    try:
        number = float(value)
    except OverflowError:
        raise ValueError(f"{name} exceeds the supported numeric range") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return number


def _finite_result(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Result exceeds the supported numeric range")
    return value


def safety_stock(demand_std: float, lead_time: float, z_score: float = 1.65) -> int:
    """Return buffer stock, rounded up to whole units.

    Uses z * demand_std * sqrt(lead_time). Demand standard deviation is per
    period; lead time uses that same period (for example, days). This assumes
    independent period demand and constant lead time. The default z-score
    approximates a 95% one-sided normal cycle-service level, not a fill rate.
    """
    demand_std = _nonnegative("demand_std", demand_std)
    lead_time = _nonnegative("lead_time", lead_time)
    z_score = _nonnegative("z_score", z_score)
    return math.ceil(_finite_result(z_score * demand_std * math.sqrt(lead_time)))


def reorder_point(
    daily_demand: float, lead_time: float, safety_stock: float = 0
) -> int:
    """Return daily demand * lead-time days + buffer stock, rounded up.

    Compare this threshold with inventory position: on-hand stock plus
    on-order stock minus backorders. Inputs must use the same stock unit.
    """
    daily_demand = _nonnegative("daily_demand", daily_demand)
    lead_time = _nonnegative("lead_time", lead_time)
    safety_stock = _nonnegative("safety_stock", safety_stock)
    return math.ceil(_finite_result(daily_demand * lead_time + safety_stock))


def inventory_turnover(cogs: float, average_inventory: float) -> float:
    """Return cost of goods sold / average inventory value for one period.

    Use matching currencies and cost bases for both values. Average inventory
    must be positive; zero cost of goods sold returns zero turnover.
    """
    cogs = _nonnegative("cogs", cogs)
    average_inventory = _nonnegative("average_inventory", average_inventory)
    if average_inventory == 0:
        raise ValueError("average_inventory must be positive")
    return _finite_result(cogs / average_inventory)
