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
    speedy_cost: Decimal = Decimal("0")


@dataclass(frozen=True)
class PricingResult:
    items: list[PricedParcel]
    total_cost: Decimal
    speedy_shipping: list[Decimal] = None
    discounts: list = None
    discount_saving: Decimal = Decimal("0")

    def __post_init__(self):
        if self.discounts is None:
            object.__setattr__(self, 'discounts', [])
        if self.speedy_shipping is None:
            object.__setattr__(self, 'speedy_shipping', [])


@dataclass(frozen=True)
class Discount:
    name: str
    saving: Decimal


class ParcelPricer:
    def price_parcel(self, parcel: Parcel, speedy: bool = False) -> PricedParcel:
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
        base_cost = calc_cost(best)
        speedy_price = base_cost if speedy else Decimal("0")
        return PricedParcel(parcel_type=best, cost=base_cost, overweight_cost=over_cost, speedy_cost=speedy_price)

    def price_order(self, parcels: list[Parcel], speedy: list[bool] | bool = None) -> PricingResult:
        if speedy is None:
            speedy = [False] * len(parcels)
        elif isinstance(speedy, bool):
            speedy = [speedy] * len(parcels)
        elif len(speedy) != len(parcels):
            raise ValueError("speedy list must have the same length as parcels list")

        priced_items = [self.price_parcel(parcel, speedy[i]) for i, parcel in enumerate(parcels)]

        # 判断订单类型：所有包裹都是 SMALL 则是 SMALL，都是 MEDIUM 则是 MEDIUM，否则是 OTHER
        if all(p.parcel_type == ParcelType.SMALL for p in priced_items):
            order_type = ParcelType.SMALL
            group_size = 4
        elif all(p.parcel_type == ParcelType.MEDIUM for p in priced_items):
            order_type = ParcelType.MEDIUM
            group_size = 3
        else:
            order_type = "Other"
            group_size = 5

        label = "Small parcel" if order_type == ParcelType.SMALL else "Medium parcel" if order_type == ParcelType.MEDIUM else "Mixed"

        def calc_group_savings(items: list[PricedParcel], group_size: int, label: str) -> tuple[Decimal, list[Discount], list[int]]:
            savings = Decimal("0")
            discounts = []
            free_indices = []
            for i in range(0, len(items), group_size):
                group = items[i:i + group_size]
                if len(group) == group_size:
                    free_item_idx = i + group.index(min(group, key=lambda x: x.cost))
                    free = items[free_item_idx]
                    savings += free.cost
                    discounts.append(Discount(name=f"{label} mania ({group_size} parcels)", saving=free.cost))
                    free_indices.append(free_item_idx)
            return savings, discounts, free_indices

        base_total = sum((item.cost for item in priced_items), start=Decimal("0"))
        discount_total, final_discounts, free_indices = calc_group_savings(priced_items, group_size, label)

        # 将免费包裹的 speedy_cost 设为 0
        for idx in free_indices:
            priced_items[idx] = PricedParcel(
                parcel_type=priced_items[idx].parcel_type,
                cost=priced_items[idx].cost,
                overweight_cost=priced_items[idx].overweight_cost,
                speedy_cost=Decimal("0")
            )

        speedy_shipping_cost = sum((item.speedy_cost for item in priced_items), start=Decimal("0"))
        after_discount = base_total - discount_total
        total = after_discount + speedy_shipping_cost

        return PricingResult(
            items=priced_items,
            total_cost=total,
            speedy_shipping=speedy_shipping_cost,
            discounts=final_discounts,
            discount_saving=discount_total
        )