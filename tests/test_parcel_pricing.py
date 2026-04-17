# test_parcel_pricing.py
from decimal import Decimal

import pytest

from src.parcel_pricing import Parcel, ParcelPricer, ParcelType


def test_prices_small_parcel():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(9, 9, 9))

    assert result.parcel_type == ParcelType.SMALL
    assert result.cost == Decimal("3")


def test_prices_medium_parcel_at_small_boundary():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(10, 9, 9))

    assert result.parcel_type == ParcelType.MEDIUM
    assert result.cost == Decimal("8")


def test_prices_medium_parcel():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(49, 20, 30))

    assert result.parcel_type == ParcelType.MEDIUM
    assert result.cost == Decimal("8")


def test_prices_large_parcel_at_medium_boundary():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(50, 40, 30))

    assert result.parcel_type == ParcelType.LARGE
    assert result.cost == Decimal("15")


def test_prices_large_parcel():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(99, 20, 20))

    assert result.parcel_type == ParcelType.LARGE
    assert result.cost == Decimal("15")


def test_prices_xl_parcel_at_large_boundary():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(100, 20, 20))

    assert result.parcel_type == ParcelType.XL
    assert result.cost == Decimal("25")


def test_prices_xl_parcel():
    pricer = ParcelPricer()

    result = pricer.price_parcel(Parcel(120, 30, 30))

    assert result.parcel_type == ParcelType.XL
    assert result.cost == Decimal("25")


def test_prices_multiple_parcels_and_total():
    pricer = ParcelPricer()

    result = pricer.price_order(
        [
            Parcel(5, 5, 5),      # Small -> 3
            Parcel(20, 20, 20),   # Medium -> 8
            Parcel(70, 30, 30),   # Large -> 15
            Parcel(120, 1, 1),    # XL -> 25
        ]
    )

    assert len(result.items) == 4
    assert [item.parcel_type for item in result.items] == [
        ParcelType.SMALL,
        ParcelType.MEDIUM,
        ParcelType.LARGE,
        ParcelType.XL,
    ]
    assert result.total_cost == Decimal("51")


@pytest.mark.parametrize("length,width,height", [
    (0, 1, 1),
    (-1, 1, 1),
    (1, 0, 1),
    (1, 1, -5),
])
def test_invalid_dimensions_raise(length, width, height):
    with pytest.raises(ValueError):
        Parcel(length, width, height)