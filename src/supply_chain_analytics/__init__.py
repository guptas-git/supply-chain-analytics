"""Dependency-free inventory calculations for supply-chain analysis."""

from .inventory import inventory_turnover, reorder_point, safety_stock

__version__ = "0.1.0"
__all__ = ["safety_stock", "reorder_point", "inventory_turnover"]
