"""Run after installing the package: python examples/inventory_basics.py."""

from supply_chain_analytics import inventory_turnover, reorder_point, safety_stock

buffer = safety_stock(demand_std=10, lead_time=4)
threshold = reorder_point(daily_demand=100, lead_time=7, safety_stock=200)
turnover = inventory_turnover(cogs=10000, average_inventory=2000)

print(f"Safety stock: {buffer} units")
print(f"Reorder point: {threshold} units")
print(f"Inventory turnover: {turnover:.1f} times per period")
