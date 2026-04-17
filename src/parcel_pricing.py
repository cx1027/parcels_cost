# parcel_pricing.py
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ParcelType(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    XL = "XL"


@dataclass(frozen=True)
class Parcel:
    length_cm: float
    width_cm: float
    height_cm: float

    def __post_init__(self) -> None:
        for name, value in (
            ("length_cm", self.length_cm),
            ("width_cm", self.width_cm),
            ("height_cm", self.height_cm),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0")


@dataclass(frozen=True)
class PricedParcel:
    parcel_type: ParcelType
    cost: Decimal


@dataclass(frozen=True)
class PricingResult:
    items: list[PricedParcel]
    total_cost: Decimal
    speedy_shipping: Decimal = Decimal("0")


class ParcelPricer:
    def price_parcel(self, parcel: Parcel) -> PricedParcel:
        max_dimension = max(parcel.length_cm, parcel.width_cm, parcel.height_cm)

        if max_dimension < 10:
            return PricedParcel(ParcelType.SMALL, Decimal("3"))
        if max_dimension < 50:
            return PricedParcel(ParcelType.MEDIUM, Decimal("8"))
        if max_dimension < 100:
            return PricedParcel(ParcelType.LARGE, Decimal("15"))
        return PricedParcel(ParcelType.XL, Decimal("25"))

    def price_order(self, parcels: list[Parcel], speedy: bool = False) -> PricingResult:
        priced_items = [self.price_parcel(parcel) for parcel in parcels]
        base_total = sum((item.cost for item in priced_items), start=Decimal("0"))
        speedy_cost = base_total if speedy else Decimal("0")
        total = base_total + speedy_cost
        return PricingResult(items=priced_items, total_cost=total, speedy_shipping=speedy_cost)