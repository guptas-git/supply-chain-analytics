"""Reference examples, rounding boundaries, assumptions and input validation."""

from importlib.metadata import version

import pytest

from supply_chain_analytics import (
    __version__,
    inventory_turnover,
    reorder_point,
    safety_stock,
)


def test_reference_examples():
    assert safety_stock(10, 4, 1.65) == 33
    assert reorder_point(100, 7, 200) == 900
    assert inventory_turnover(10000, 2000) == 5.0


def test_defaults_and_keyword_arguments():
    assert safety_stock(demand_std=10, lead_time=4) == 33
    assert reorder_point(daily_demand=100, lead_time=7) == 700


def test_fractional_stock_rounds_up():
    assert safety_stock(1.1, 1, 1) == 2
    assert reorder_point(0.25, 3) == 1
    assert reorder_point(0, 0, 0.1) == 1


def test_zero_inputs():
    assert safety_stock(0, 4) == 0
    assert safety_stock(10, 0) == 0
    assert safety_stock(10, 4, 0) == 0
    assert reorder_point(0, 7, 200) == 200
    assert reorder_point(100, 0) == 0
    assert inventory_turnover(0, 2000) == 0.0


def test_demand_variability_accumulates_with_square_root_of_time():
    assert safety_stock(10, 4, 1) == 2 * safety_stock(10, 1, 1)
    assert safety_stock(10, 0.25, 1) == 5


def test_turnover_uses_matching_value_units():
    assert inventory_turnover(10000, 2000) == inventory_turnover(100, 20)


INPUTS = [
    (safety_stock, {"demand_std": 10, "lead_time": 4}, "demand_std"),
    (safety_stock, {"demand_std": 10, "lead_time": 4}, "lead_time"),
    (safety_stock, {"demand_std": 10, "lead_time": 4}, "z_score"),
    (reorder_point, {"daily_demand": 100, "lead_time": 7}, "daily_demand"),
    (reorder_point, {"daily_demand": 100, "lead_time": 7}, "lead_time"),
    (reorder_point, {"daily_demand": 100, "lead_time": 7}, "safety_stock"),
    (inventory_turnover, {"cogs": 10000, "average_inventory": 2000}, "cogs"),
    (inventory_turnover, {"cogs": 10000, "average_inventory": 2000}, "average_inventory"),
]


@pytest.mark.parametrize("function,kwargs,parameter", INPUTS)
@pytest.mark.parametrize("bad_value", [-1, float("nan"), float("inf"), -float("inf")])
def test_negative_and_nonfinite_inputs(function, kwargs, parameter, bad_value):
    with pytest.raises(ValueError, match=parameter):
        function(**{**kwargs, parameter: bad_value})


@pytest.mark.parametrize("function,kwargs,parameter", INPUTS)
@pytest.mark.parametrize("bad_value", [True, "10", None])
def test_non_numeric_inputs_are_not_coerced(function, kwargs, parameter, bad_value):
    with pytest.raises(TypeError, match=parameter):
        function(**{**kwargs, parameter: bad_value})


def test_zero_average_inventory_is_rejected():
    with pytest.raises(ValueError, match="average_inventory must be positive"):
        inventory_turnover(10000, 0)


@pytest.mark.parametrize(
    "function,args",
    [
        (safety_stock, (1e308, 4, 2)),
        (reorder_point, (1e308, 4)),
        (inventory_turnover, (1e308, 1e-308)),
    ],
)
def test_overflow_cannot_return_infinite_stock_or_turnover(function, args):
    with pytest.raises(ValueError, match="supported numeric range"):
        function(*args)


def test_integer_outside_float_range_is_rejected():
    with pytest.raises(ValueError, match="demand_std"):
        safety_stock(10**1000, 1)


def test_installed_version_matches_public_version():
    assert __version__ == version("supply-chain-analytics") == "0.1.0"
