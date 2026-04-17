# parcel_pricing.py
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ParcelType(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    XL = "XL"

    @property
    def weight_limit_kg(self) -> float:
        limits = {
            ParcelType.SMALL: 1.0,
            ParcelType.MEDIUM: 3.0,
            ParcelType.LARGE: 6.0,
            ParcelType.XL: 10.0,
        }
        return limits[self]

    @property
    def base_cost(self) -> Decimal:
        costs = {
            ParcelType.SMALL: Decimal("3"),
            ParcelType.MEDIUM: Decimal("8"),
            ParcelType.LARGE: Decimal("15"),
            ParcelType.XL: Decimal("25"),
        }
        return costs[self]


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
    OVERWEIGHT_COST_PER_KG = Decimal("2")

    def price_parcel(self, parcel: Parcel) -> PricedParcel:
        max_dimension = max(parcel.length_cm, parcel.width_cm, parcel.height_cm)

        if max_dimension < 10:
            parcel_type = ParcelType.SMALL
        elif max_dimension < 50:
            parcel_type = ParcelType.MEDIUM
        elif max_dimension < 100:
            parcel_type = ParcelType.LARGE
        else:
            parcel_type = ParcelType.XL

        base_cost = parcel_type.base_cost
        weight_limit = parcel_type.weight_limit_kg
        overweight_kg = max(0.0, parcel.weight_kg - weight_limit)
        overweight_cost = self.OVERWEIGHT_COST_PER_KG * Decimal(str(overweight_kg))
        total_cost = base_cost + overweight_cost

        return PricedParcel(parcel_type=parcel_type, cost=total_cost, overweight_cost=overweight_cost)

    def price_order(self, parcels: list[Parcel], speedy: bool = False) -> PricingResult:
        priced_items = [self.price_parcel(parcel) for parcel in parcels]
        base_total = sum((item.cost for item in priced_items), start=Decimal("0"))
        speedy_cost = base_total if speedy else Decimal("0")
        total = base_total + speedy_cost
        return PricingResult(items=priced_items, total_cost=total, speedy_shipping=speedy_cost)