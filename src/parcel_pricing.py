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
        base_total = sum((item.cost for item in priced_items), start=Decimal("0"))
        speedy_cost = base_total if speedy else Decimal("0")
        total = base_total + speedy_cost
        return PricingResult(items=priced_items, total_cost=total, speedy_shipping=speedy_cost)