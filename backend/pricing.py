"""Unit-price policies applied before the booking price is saved."""

from dataclasses import dataclass
from typing import Protocol


class PricingPolicy(Protocol):
    def unit_price(self, list_price: int) -> int: ...


class StandardPrice:
    def unit_price(self, list_price: int) -> int:
        return list_price


@dataclass(frozen=True)
class PercentageDiscount:
    percent: int

    def __post_init__(self):
        if type(self.percent) is not int or not 1 <= self.percent <= 99:
            raise ValueError("Mức giảm phải là số nguyên từ 1 đến 99.")

    def unit_price(self, list_price: int) -> int:
        return max(1, list_price * (100 - self.percent) // 100)


def pricing_from_percent(value: str | int | None) -> PricingPolicy:
    if value is None:
        return StandardPrice()
    if isinstance(value, str):
        value = value.strip()
        if not value or value == "0":
            return StandardPrice()
        if not value.isdigit():
            raise ValueError("Mức giảm phải là số nguyên từ 0 đến 99.")
        value = int(value)
    if type(value) is not int or not 0 <= value <= 99:
        raise ValueError("Mức giảm phải là số nguyên từ 0 đến 99.")
    return StandardPrice() if value == 0 else PercentageDiscount(value)
