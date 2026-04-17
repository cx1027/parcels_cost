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
    # Only MEDIUM fits physically, plus HEAVY. Cheapest is Medium($8).
    assert result.parcel_type == ParcelType.MEDIUM
    assert result.cost == Decimal("8")


def test_prices_medium_parcel():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(49, 20, 30))
    # Only MEDIUM fits physically, plus HEAVY. Cheapest is Medium($8).
    assert result.parcel_type == ParcelType.MEDIUM
    assert result.cost == Decimal("8")


def test_prices_large_parcel_at_medium_boundary():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(50, 40, 30))
    # Only LARGE fits physically, plus HEAVY. Cheapest is Large($15).
    assert result.parcel_type == ParcelType.LARGE
    assert result.cost == Decimal("15")


def test_prices_large_parcel():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(99, 20, 20))
    # Only LARGE fits physically, plus HEAVY. Cheapest is Large($15).
    assert result.parcel_type == ParcelType.LARGE
    assert result.cost == Decimal("15")


def test_prices_xl_parcel_at_large_boundary():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(100, 20, 20))
    # Only XL fits physically, plus HEAVY. Cheapest is XL($25).
    assert result.parcel_type == ParcelType.XL
    assert result.cost == Decimal("25")


def test_prices_xl_parcel():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(120, 30, 30))
    # Only XL fits physically, plus HEAVY. Cheapest is XL($25).
    assert result.parcel_type == ParcelType.XL
    assert result.cost == Decimal("25")


def test_prices_multiple_parcels_and_total():
    pricer = ParcelPricer()

    result = pricer.price_order(
        [
            Parcel(5, 5, 5),      # Small dims -> Small -> 3
            Parcel(20, 20, 20),   # Medium dims -> Medium -> 8
            Parcel(70, 30, 30),   # Large dims -> Large -> 15
            Parcel(120, 1, 1),    # XL dims -> XL -> 25
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
    assert result.speedy_shipping == Decimal("0")


def test_speedy_shipping_cost_equals_base_total():
    pricer = ParcelPricer()

    result = pricer.price_order(
        [
            Parcel(5, 5, 5),      # Small dims -> Small -> 3
            Parcel(20, 20, 20),   # Medium dims -> Medium -> 8
        ],
        speedy=True,
    )

    assert result.speedy_shipping == Decimal("11")
    assert result.total_cost == Decimal("22")


def test_speedy_shipping_no_impact_on_individual_parcel_cost():
    pricer = ParcelPricer()

    result = pricer.price_order(
        [
            Parcel(5, 5, 5),      # Small dims -> Small -> 3
            Parcel(20, 20, 20),   # Medium dims -> Medium -> 8
        ],
        speedy=True,
    )

    assert result.items[0].cost == Decimal("3")
    assert result.items[1].cost == Decimal("8")


@pytest.mark.parametrize("length,width,height", [
    (0, 1, 1),
    (-1, 1, 1),
    (1, 0, 1),
    (1, 1, -5),
])
def test_invalid_dimensions_raise(length, width, height):
    with pytest.raises(ValueError):
        Parcel(length, width, height)


def test_invalid_weight_raises():
    with pytest.raises(ValueError):
        Parcel(5, 5, 5, weight_kg=-1)


def test_small_parcel_at_weight_limit_no_overweight():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(9, 9, 9, weight_kg=1.0))
    assert result.parcel_type == ParcelType.SMALL
    assert result.cost == Decimal("3")
    assert result.overweight_cost == Decimal("0")


def test_small_parcel_over_weight_limit():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(9, 9, 9, weight_kg=2.0))
    assert result.parcel_type == ParcelType.SMALL
    assert result.cost == Decimal("5")
    assert result.overweight_cost == Decimal("2")


def test_small_parcel_over_weight_limit_multiple_kg():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(9, 9, 9, weight_kg=4.0))
    assert result.parcel_type == ParcelType.SMALL
    assert result.cost == Decimal("9")
    assert result.overweight_cost == Decimal("6")


def test_medium_parcel_over_weight_limit():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(20, 20, 20, weight_kg=5.0))
    # Only MEDIUM fits physically, plus HEAVY. Medium: $8 + $2×(5-3) = $12. Heavy: $50. Cheapest is Medium.
    assert result.parcel_type == ParcelType.MEDIUM
    assert result.cost == Decimal("12")
    assert result.overweight_cost == Decimal("4")


def test_large_parcel_over_weight_limit():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(70, 30, 30, weight_kg=8.0))
    # Only LARGE fits physically, plus HEAVY. Large: $15 + $2×(8-6) = $19. Heavy: $50. Cheapest is Large.
    assert result.parcel_type == ParcelType.LARGE
    assert result.cost == Decimal("19")
    assert result.overweight_cost == Decimal("4")


def test_xl_parcel_over_weight_limit():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(120, 1, 1, weight_kg=15.0))
    # Only XL fits physically, plus HEAVY. XL: $25 + $2×(15-10) = $35. Heavy: $50. Cheapest is XL.
    assert result.parcel_type == ParcelType.XL
    assert result.cost == Decimal("35")
    assert result.overweight_cost == Decimal("10")


def test_order_with_overweight_and_speedy():
    pricer = ParcelPricer()
    result = pricer.price_order(
        [
            Parcel(5, 5, 5, weight_kg=4.0),      # Small dims -> Small: 3+6=9
            Parcel(20, 20, 20, weight_kg=5.0),   # Medium dims -> Medium: 8+4=12
        ],
        speedy=True,
    )
    base_total = Decimal("9") + Decimal("12")
    assert result.items[0].overweight_cost == Decimal("6")
    assert result.items[1].overweight_cost == Decimal("4")
    assert result.speedy_shipping == base_total
    assert result.total_cost == base_total * 2


def test_prices_xl_parcel_at_dimension_boundary():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(120, 30, 30))
    # Only XL fits physically, plus HEAVY. XL: $25. Heavy: $50. Cheapest is XL.
    assert result.parcel_type == ParcelType.XL
    assert result.cost == Decimal("25")


def test_heavy_triggered_by_weight_small_parcel():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(9, 9, 9, weight_kg=50.0))
    assert result.parcel_type == ParcelType.HEAVY
    assert result.cost == Decimal("50")
    assert result.overweight_cost == Decimal("0")


def test_heavy_triggered_by_weight_medium_parcel():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(20, 20, 20, weight_kg=55.0))
    assert result.parcel_type == ParcelType.HEAVY
    assert result.cost == Decimal("55")
    assert result.overweight_cost == Decimal("5")


def test_heavy_triggered_by_weight_xl_parcel():
    pricer = ParcelPricer()
    result = pricer.price_parcel(Parcel(120, 1, 1, weight_kg=70.0))
    assert result.parcel_type == ParcelType.HEAVY
    assert result.cost == Decimal("70")
    assert result.overweight_cost == Decimal("20")


def test_order_with_heavy_and_speedy():
    pricer = ParcelPricer()
    result = pricer.price_order(
        [
            Parcel(9, 9, 9, weight_kg=60.0),      # Small dims, but weight >= 50 -> Heavy +10kg overweight -> 50+10=60
            Parcel(20, 20, 20, weight_kg=55.0),     # Medium dims, but weight >= 50 -> Heavy +5kg overweight -> 50+5=55
        ],
        speedy=True,
    )
    base_total = Decimal("60") + Decimal("55")
    assert result.items[0].parcel_type == ParcelType.HEAVY
    assert result.items[1].parcel_type == ParcelType.HEAVY
    assert result.items[0].overweight_cost == Decimal("10")
    assert result.items[1].overweight_cost == Decimal("5")
    assert result.speedy_shipping == base_total
    assert result.total_cost == base_total * 2


def test_small_mania_every_4th_free():
    """Small parcel mania: every 4th small parcel is free"""
    pricer = ParcelPricer()
    # 4 small parcels, all cost $3 -> one should be free (saving $3)
    result = pricer.price_order([
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
    ])
    assert result.total_cost == Decimal("9")  # 3 * $3
    assert result.discount_saving == Decimal("3")
    assert len(result.discounts) == 1
    assert "Small parcel mania" in result.discounts[0].name


def test_medium_mania_every_3rd_free():
    """Medium parcel mania: every 3rd medium parcel is free"""
    pricer = ParcelPricer()
    # 3 medium parcels, all cost $8 -> one should be free (saving $8)
    result = pricer.price_order([
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
    ])
    assert result.total_cost == Decimal("16")  # 2 * $8
    assert result.discount_saving == Decimal("8")
    assert len(result.discounts) == 1
    assert "Medium parcel mania" in result.discounts[0].name


def test_mixed_mania_every_5th_free():
    """Mixed parcel mania: every 5th parcel of any type is free"""
    pricer = ParcelPricer()
    # 5 parcels of mixed types -> one should be free (cheapest is $3)
    result = pricer.price_order([
        Parcel(5, 5, 5),       # Small $3
        Parcel(5, 5, 5),       # Small $3
        Parcel(5, 5, 5),       # Small $3
        Parcel(20, 20, 20),    # Medium $8
        Parcel(20, 20, 20),    # Medium $8
    ])
    assert result.total_cost == Decimal("22")  # (3+3+3+8+8) - 3 = 22
    assert result.discount_saving == Decimal("3")
    assert len(result.discounts) == 1
    assert "Mixed mania" in result.discounts[0].name


def test_small_mania_with_multiple_groups():
    """8 small parcels -> 2 groups of 4, 2 parcels free"""
    pricer = ParcelPricer()
    result = pricer.price_order([
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
    ])
    assert result.total_cost == Decimal("18")  # 8*3 - 2*3 = 18
    assert result.discount_saving == Decimal("6")  # 2 parcels free
    assert len(result.discounts) == 2


def test_medium_mania_with_multiple_groups():
    """6 medium parcels -> 2 groups of 3, 2 parcels free"""
    pricer = ParcelPricer()
    result = pricer.price_order([
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
        Parcel(20, 20, 20),
    ])
    assert result.total_cost == Decimal("32")  # 6*8 - 2*8 = 32
    assert result.discount_saving == Decimal("16")  # 2 parcels free



def test_optimal_discount_medium_parcels():
    """Example: 6x medium parcels. 3x $8, 3x $10 -> saves $18"""
    pricer = ParcelPricer()
    parcels = [
        Parcel(20, 20, 20, weight_kg=0),   # $8 (within 3kg limit)
        Parcel(20, 20, 20, weight_kg=0),   # $8
        Parcel(20, 20, 20, weight_kg=0),   # $8
        Parcel(20, 20, 20, weight_kg=4.0), # $8 + 2*1 = $10 (1kg overweight)
        Parcel(20, 20, 20, weight_kg=4.0), # $10
        Parcel(20, 20, 20, weight_kg=4.0), # $10
    ]
    result = pricer.price_order(parcels)
    # DP finds optimal grouping: Group 1: [3x$8], Group 2: [3x$10]
    # Saves: $8 + $10 = $18
    # Total: 3*8 + 3*10 - 18 = 24 + 30 - 18 = 36
    assert result.discount_saving == Decimal("18")
    assert result.total_cost == Decimal("36")


def test_discounts_and_speedy_combined():
    """Speedy shipping applies after discounts"""
    pricer = ParcelPricer()
    # 4 small parcels = 1 small mania, save $3
    result = pricer.price_order([
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
        Parcel(5, 5, 5),
    ], speedy=True)
    # Base: 4*3 = 12
    # After discount: 12 - 3 = 9
    # Speedy: 9
    # Total: 9 + 9 = 18
    assert result.total_cost == Decimal("18")
    assert result.discount_saving == Decimal("3")
    assert result.speedy_shipping == Decimal("9")


def test_each_parcel_used_only_once():
    """A parcel can only be used in one discount"""
    pricer = ParcelPricer()
    # 4 small + 1 medium = 5 total
    # Could form: 1 small mania (4 small) OR 1 mixed mania (5 parcels)
    # Small mania saves $3, mixed saves cheapest of all 5 = $3
    # Both save the same, but small mania uses only small
    result = pricer.price_order([
        Parcel(5, 5, 5),  # Small $3
        Parcel(5, 5, 5),  # Small $3
        Parcel(5, 5, 5),  # Small $3
        Parcel(5, 5, 5),  # Small $3
        Parcel(20, 20, 20),  # Medium $8
    ])
    # Small mania saves $3, mixed would also save $3
    # Our DP should find optimal
    # If small mania: 3 small paid + 1 small free + 1 medium paid = 3*3 + 8 = 17
    # If mixed: 4 small + 1 medium = $20 total, cheapest $3 free = $17
    # Both give $17, either is valid
    assert result.total_cost == Decimal("17")


def test_large_and_xl_in_mixed_mania():
    """Large and XL parcels can be used in mixed mania"""
    pricer = ParcelPricer()
    result = pricer.price_order([
        Parcel(5, 5, 5),       # Small $3
        Parcel(20, 20, 20),    # Medium $8
        Parcel(70, 30, 30),    # Large $15
        Parcel(120, 1, 1),     # XL $25
        Parcel(5, 5, 5),       # Small $3 -> 5th parcel, cheapest $3 free
    ])
    # 5 parcels: $3 + $8 + $15 + $25 + $3 = $54
    # Mixed mania saves cheapest $3
    # Total: 54 - 3 = 51
    assert result.discount_saving == Decimal("3")
    assert result.total_cost == Decimal("51")
    assert len(result.discounts) == 1