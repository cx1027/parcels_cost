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
class Discount:
    discount_type: str
    parcel_indices: frozenset[int]
    saving: Decimal

    def __repr__(self) -> str:
        return f"Discount({self.discount_type}, indices={set(self.parcel_indices)}, saving={self.saving})"


@dataclass(frozen=True)
class DiscountResult:
    discounts: list[Discount]
    total_saving: Decimal


@dataclass(frozen=True)
class PricingResult:
    items: list[PricedParcel]
    total_cost: Decimal
    speedy_shipping: Decimal = Decimal("0")
    discounted_savings: Decimal = Decimal("0")


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

    def _find_groups(
        self,
        priced: list[PricedParcel],
        type_filter: ParcelType | None,
        group_size: int,
    ) -> list[frozenset[int]]:
        indices = [i for i, p in enumerate(priced) if type_filter is None or p.parcel_type == type_filter]
        groups: list[frozenset[int]] = []

        def backtrack(start: int, chosen: list[int]) -> None:
            if len(chosen) == group_size:
                groups.append(frozenset(chosen))
                return
            for i in range(start, len(indices)):
                chosen.append(indices[i])
                backtrack(i + 1, chosen)
                chosen.pop()

        backtrack(0, [])
        return groups

    def _calc_saving(self, priced: list[PricedParcel], group: frozenset[int]) -> Decimal:
        costs = [priced[i].cost for i in group]
        return min(costs)

    def _search_best_discounts(
        self,
        priced: list[PricedParcel],
    ) -> DiscountResult:
        discount_defs = [
            ("Small Mania (4th free)", ParcelType.SMALL, 4),
            ("Medium Mania (3rd free)", ParcelType.MEDIUM, 3),
            ("Mixed Mania (5th free)", None, 5),
        ]

        all_groups: list[tuple[str, frozenset[int], Decimal]] = []
        for label, ptype, size in discount_defs:
            groups = self._find_groups(priced, ptype, size)
            for g in groups:
                all_groups.append((label, g, self._calc_saving(priced, g)))

        if not all_groups:
            return DiscountResult(discounts=[], total_saving=Decimal("0"))

        n = len(all_groups)
        best_saving = Decimal("0")
        best_discounts: list[Discount] = []

        for mask in range(1, 1 << n):
            used: set[int] = set()
            selected: list[Discount] = []
            total = Decimal("0")

            for j in range(n):
                if (mask >> j) & 1:
                    label, group, saving = all_groups[j]
                    if not used.isdisjoint(group):
                        break
                    used.update(group)
                    selected.append(Discount(label, group, saving))
                    total += saving
            else:
                if total > best_saving:
                    best_saving = total
                    best_discounts = selected

        return DiscountResult(discounts=best_discounts, total_saving=best_saving)

    def price_order(self, parcels: list[Parcel], speedy: bool = False) -> PricingResult:
        priced_items = [self.price_parcel(parcel) for parcel in parcels]
        base_total = sum((item.cost for item in priced_items), start=Decimal("0"))

        disc_result = self._search_best_discounts(priced_items)
        discounted_total = base_total - disc_result.total_saving
        speedy_cost = discounted_total if speedy else Decimal("0")
        total = discounted_total + speedy_cost

        return PricingResult(
            items=priced_items,
            total_cost=total,
            speedy_shipping=speedy_cost,
            discounted_savings=disc_result.total_saving,
        )