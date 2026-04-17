# parcel_pricing.py
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ParcelType(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    XL = "XL"
    HEAVY = "Heavy"

    @property
    def weight_limit_kg(self) -> float:
        return {
            ParcelType.SMALL: 1.0,
            ParcelType.MEDIUM: 3.0,
            ParcelType.LARGE: 6.0,
            ParcelType.XL: 10.0,
            ParcelType.HEAVY: 50.0,
        }[self]

    @property
    def base_cost(self) -> Decimal:
        return {
            ParcelType.SMALL: Decimal("3"),
            ParcelType.MEDIUM: Decimal("8"),
            ParcelType.LARGE: Decimal("15"),
            ParcelType.XL: Decimal("25"),
            ParcelType.HEAVY: Decimal("50"),
        }[self]

    @property
    def overweight_cost_per_kg(self) -> Decimal:
        return {
            ParcelType.SMALL: Decimal("2"),
            ParcelType.MEDIUM: Decimal("2"),
            ParcelType.LARGE: Decimal("2"),
            ParcelType.XL: Decimal("2"),
            ParcelType.HEAVY: Decimal("1"),
        }[self]


@dataclass(frozen=True)
class Parcel:
    length_cm: float
    width_cm: float
    height_cm: float
    weight_kg: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("length_cm", self.length_cm),
            ("width_cm", self.width_cm),
            ("height_cm", self.height_cm),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0")
        if self.weight_kg < 0:
            raise ValueError("weight_kg must be greater than or equal to 0")


@dataclass(frozen=True)
class PricedParcel:
    parcel_type: ParcelType
    cost: Decimal
    overweight_cost: Decimal = Decimal("0")


@dataclass(frozen=True)
class PricingResult:
    items: list[PricedParcel]
    total_cost: Decimal
    speedy_shipping: Decimal = Decimal("0")
    discounts: list = None
    discount_saving: Decimal = Decimal("0")

    def __post_init__(self):
        if self.discounts is None:
            object.__setattr__(self, 'discounts', [])


@dataclass(frozen=True)
class Discount:
    name: str
    saving: Decimal


class ParcelPricer:
    def price_parcel(self, parcel: Parcel) -> PricedParcel:
        max_dimension = max(parcel.length_cm, parcel.width_cm, parcel.height_cm)

        if max_dimension >= 100:
            dimension_types = [ParcelType.XL]
        elif max_dimension >= 50:
            dimension_types = [ParcelType.LARGE]
        elif max_dimension >= 10:
            dimension_types = [ParcelType.MEDIUM]
        else:
            dimension_types = [ParcelType.SMALL]

        def calc_cost(pt: ParcelType) -> Decimal:
            limit = pt.weight_limit_kg
            over = max(0.0, parcel.weight_kg - limit)
            return pt.base_cost + pt.overweight_cost_per_kg * Decimal(str(over))

        candidates = dimension_types + [ParcelType.HEAVY]
        best = min(candidates, key=calc_cost)
        over_kg = max(0.0, parcel.weight_kg - best.weight_limit_kg)
        over_cost = best.overweight_cost_per_kg * Decimal(str(over_kg))
        return PricedParcel(parcel_type=best, cost=calc_cost(best), overweight_cost=over_cost)

    def price_order(self, parcels: list[Parcel], speedy: bool = False) -> PricingResult:
        priced_items = [self.price_parcel(parcel) for parcel in parcels]

        # Categorize by type
        small = [p for p in priced_items if p.parcel_type == ParcelType.SMALL]
        medium = [p for p in priced_items if p.parcel_type == ParcelType.MEDIUM]
        other = [p for p in priced_items if p.parcel_type not in (ParcelType.SMALL, ParcelType.MEDIUM)]

        # Sort each type by cost for optimal grouping
        sorted_small = sorted(small, key=lambda x: x.cost)
        sorted_medium = sorted(medium, key=lambda x: x.cost)

        def calc_mixed_savings(remaining: list) -> tuple[Decimal, list]:
            sorted_rem = sorted(remaining, key=lambda x: x.cost)
            savings = Decimal("0")
            discount_items = []
            while len(sorted_rem) >= 5:
                group = sorted_rem[:5]
                free_saving = group[0].cost
                savings += free_saving
                discount_items.append(Discount(
                    name=f"Mixed mania (5 parcels)",
                    saving=free_saving
                ))
                sorted_rem = sorted_rem[5:]
            return savings, discount_items

        # DP for small and medium manias
        # State: (small_used, medium_used) = max savings, and path to reconstruct
        n_small = len(sorted_small)
        n_medium = len(sorted_medium)

        # dp[si][mi] = (max_saving, path_info)
        # path_info: list of (type, count)
        dp = [[(Decimal("0"), []) for _ in range(n_medium + 1)] for _ in range(n_small + 1)]

        for si in range(n_small + 1):
            for mi in range(n_medium + 1):
                curr_saving, curr_path = dp[si][mi]

                # Try adding small mania (uses 4 small)
                if si >= 4:
                    new_saving = dp[si - 4][mi][0] + sorted_small[si - 4].cost
                    new_path = dp[si - 4][mi][1] + [("small", 1)]
                    if new_saving > curr_saving:
                        dp[si][mi] = (new_saving, new_path)

                # Try adding medium mania (uses 3 medium)
                if mi >= 3:
                    new_saving = dp[si][mi - 3][0] + sorted_medium[mi - 3].cost
                    new_path = dp[si][mi - 3][1] + [("medium", 1)]
                    if new_saving > curr_saving:
                        dp[si][mi] = (new_saving, new_path)

        # Get optimal small/medium mania savings
        mania_saving, mania_info = dp[n_small][n_medium]

        # Count small and medium used in their respective manias
        small_used_in_manias = sum(4 * count for mtype, count in mania_info if mtype == "small")
        medium_used_in_manias = sum(3 * count for mtype, count in mania_info if mtype == "medium")

        remaining = sorted_small[small_used_in_manias:] + sorted_medium[medium_used_in_manias:] + other
        mixed_saving, mixed_discounts = calc_mixed_savings(remaining)
        total_discount_saving = mania_saving + mixed_saving

        # Build discount details
        final_discounts = []
        # Small manias
        idx_small = 0
        for mtype, count in mania_info:
            if mtype == "small":
                for _ in range(count):
                    saving = sorted_small[idx_small].cost
                    final_discounts.append(Discount(
                        name=f"Small parcel mania (4 parcels)",
                        saving=saving
                    ))
                    idx_small += 4
        # Medium manias
        idx_medium = 0
        for mtype, count in mania_info:
            if mtype == "medium":
                for _ in range(count):
                    saving = sorted_medium[idx_medium].cost
                    final_discounts.append(Discount(
                        name=f"Medium parcel mania (3 parcels)",
                        saving=saving
                    ))
                    idx_medium += 3
        final_discounts.extend(mixed_discounts)

        base_total = sum((item.cost for item in priced_items), start=Decimal("0"))
        discount_total = sum(d.saving for d in final_discounts)
        after_discount = base_total - discount_total
        speedy_cost = after_discount if speedy else Decimal("0")
        total = after_discount + speedy_cost

        return PricingResult(
            items=priced_items,
            total_cost=total,
            speedy_shipping=speedy_cost,
            discounts=final_discounts,
            discount_saving=discount_total
        )