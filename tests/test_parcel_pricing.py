# test_parcel_pricing.py
from decimal import Decimal

import pytest

from src.parcel_pricing import Parcel, ParcelPricer, ParcelType, Discount, DiscountResult


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
    pricer = ParcelPricer()
    # 4 small parcels, each $3 -> one is free, total saving $3
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(4)])
    assert result.discounted_savings == Decimal("3")
    assert result.total_cost == Decimal("9")


def test_small_mania_with_extra():
    pricer = ParcelPricer()
    # 5 small parcels, each $3 -> one is free, total saving $3
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(5)])
    assert result.discounted_savings == Decimal("3")
    assert result.total_cost == Decimal("12")


def test_small_mania_8_parcels():
    pricer = ParcelPricer()
    # 8 small parcels, each $3 -> two are free, total saving $6
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(8)])
    assert result.discounted_savings == Decimal("6")
    assert result.total_cost == Decimal("18")


def test_medium_mania_every_3rd_free():
    pricer = ParcelPricer()
    # 3 medium parcels, each $8 -> one is free, saving $8
    result = pricer.price_order([Parcel(20, 20, 20) for _ in range(3)])
    assert result.discounted_savings == Decimal("8")
    assert result.total_cost == Decimal("16")


def test_medium_mania_6_parcels():
    pricer = ParcelPricer()
    # 6 medium parcels, each $8 -> two are free, saving $16
    result = pricer.price_order([Parcel(20, 20, 20) for _ in range(6)])
    assert result.discounted_savings == Decimal("16")
    assert result.total_cost == Decimal("32")


def test_mixed_mania_every_5th_free():
    pricer = ParcelPricer()
    # 5 mixed parcels (Small, Medium, Large, XL, Heavy) -> one is free, saving = cheapest ($3)
    result = pricer.price_order(
        [
            Parcel(5, 5, 5),      # Small $3
            Parcel(20, 20, 20),   # Medium $8
            Parcel(70, 30, 30),   # Large $15
            Parcel(120, 1, 1),    # XL $25
            Parcel(9, 9, 9, weight_kg=60.0),  # Heavy $60
        ]
    )
    assert result.discounted_savings == Decimal("3")
    assert result.total_cost == Decimal("108")


def test_cheapest_in_group_is_free():
    pricer = ParcelPricer()
    # 3 medium parcels: 2 x $8, 1 x $10 -> cheapest ($8) is free
    result = pricer.price_order(
        [
            Parcel(20, 20, 20),           # $8
            Parcel(20, 20, 20),           # $8
            Parcel(20, 20, 20, weight_kg=1.0),  # $8 + $2 = $10
        ]
    )
    assert result.discounted_savings == Decimal("8")
    assert result.total_cost == Decimal("18")


def test_discount_does_not_change_individual_prices():
    pricer = ParcelPricer()
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(4)])
    # Individual prices unchanged, only total is reduced by discount
    for item in result.items:
        assert item.cost == Decimal("3")
    assert result.total_cost == Decimal("9")  # 4*$3 - $3 discount


def test_no_discount_when_below_threshold():
    pricer = ParcelPricer()
    # 3 small parcels (threshold is 4) -> no discount
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(3)])
    assert result.discounted_savings == Decimal("0")
    assert result.total_cost == Decimal("9")


def test_discount_and_speedy_speedy_applies_after_discount():
    pricer = ParcelPricer()
    # 4 small parcels: base = $12, discount = $3, discounted = $9, speedy = $9
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(4)], speedy=True)
    assert result.discounted_savings == Decimal("3")
    assert result.total_cost == Decimal("18")  # (12 - 3) * 2


def test_example_6x_medium_parcels():
    pricer = ParcelPricer()
    # 3 x $8, 3 x $10 -> total $54
    # 1st discount (3rd-free): group 3 x $8 -> save $8
    # 2nd discount (3rd-free): group 3 x $10 -> save $10
    # Total saving = $18, total = $54 - $18 = $36
    result = pricer.price_order(
        [
            Parcel(20, 20, 20),                      # $8
            Parcel(20, 20, 20),                      # $8
            Parcel(20, 20, 20, weight_kg=1.0),        # $10
            Parcel(20, 20, 20),                      # $8
            Parcel(20, 20, 20),                      # $8
            Parcel(20, 20, 20, weight_kg=1.0),       # $10
        ]
    )
    assert result.discounted_savings == Decimal("18")
    assert result.total_cost == Decimal("36")


def test_best_combination_small_vs_mixed():
    pricer = ParcelPricer()
    # 4 small parcels, each $3
    # Option A: 1 small-mania (4th free) -> save $3
    # Option B: 1 mixed-mania (5th free) -> can't, only 4 parcels
    # Best: small-mania, save $3
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(4)])
    assert result.discounted_savings == Decimal("3")


def test_large_xl_heavy_parcels_no_mania():
    pricer = ParcelPricer()
    # Large, XL, Heavy don't have their own mania discounts
    # 3 large parcels -> no small/medium mania, no mixed (need 5)
    result = pricer.price_order(
        [
            Parcel(70, 30, 30),
            Parcel(70, 30, 30),
            Parcel(70, 30, 30),
        ]
    )
    assert result.discounted_savings == Decimal("0")
    assert result.total_cost == Decimal("45")


def test_mixed_mania_takes_cheapest_from_all():
    pricer = ParcelPricer()
    # 5 parcels: Small $3, Medium $8, Large $15, XL $25, Heavy $60
    # Mixed mania (5th free) -> cheapest ($3) is free -> save $3
    result = pricer.price_order(
        [
            Parcel(70, 30, 30),   # Large $15
            Parcel(20, 20, 20),   # Medium $8
            Parcel(5, 5, 5),      # Small $3
            Parcel(120, 1, 1),    # XL $25
            Parcel(9, 9, 9, weight_kg=60.0),  # Heavy $60
        ]
    )
    assert result.discounted_savings == Decimal("3")


def test_small_and_medium_mania_can_combine():
    pricer = ParcelPricer()
    # 4 small + 3 medium = 7 parcels
    # Small-mania: 4 small -> save $3
    # Medium-mania: 3 medium -> save $8
    # Total: $11
    result = pricer.price_order(
        [Parcel(5, 5, 5) for _ in range(4)] +
        [Parcel(20, 20, 20) for _ in range(3)]
    )
    assert result.discounted_savings == Decimal("11")
    # Base: 4*$3 + 3*$8 = $12 + $24 = $36, minus $11 = $25
    assert result.total_cost == Decimal("25")


def test_empty_order_no_discount():
    pricer = ParcelPricer()
    result = pricer.price_order([])
    assert result.discounted_savings == Decimal("0")
    assert result.total_cost == Decimal("0")


def test_single_parcel_no_discount():
    pricer = ParcelPricer()
    result = pricer.price_order([Parcel(5, 5, 5)])
    assert result.discounted_savings == Decimal("0")
    assert result.total_cost == Decimal("3")


def test_parcel_cannot_be_used_in_same_discount_twice():
    pricer = ParcelPricer()
    # 4 small, all $3 -> only one small-mania group possible (needs 4 distinct parcels)
    # Cannot make two groups of 4 from 4 parcels
    result = pricer.price_order([Parcel(5, 5, 5) for _ in range(4)])
    # Only one group possible, save $3
    assert result.discounted_savings == Decimal("3")


def test_heavy_parcel_qualifies_for_mixed_mania():
    pricer = ParcelPricer()
    # 5 parcels including Heavy
    # Mixed mania (5th free) -> cheapest is Small ($3) -> save $3
    result = pricer.price_order(
        [
            Parcel(9, 9, 9, weight_kg=60.0),   # Heavy $60
            Parcel(20, 20, 20),                 # Medium $8
            Parcel(70, 30, 30),                 # Large $15
            Parcel(5, 5, 5),                    # Small $3
            Parcel(120, 1, 1),                  # XL $25
        ]
    )
    assert result.discounted_savings == Decimal("3")