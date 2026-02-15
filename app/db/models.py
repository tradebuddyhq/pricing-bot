from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RawListing:
    title: str
    price: float
    currency: str
    shipping_cost: float
    condition: str | None
    sold: bool
    date: str | None
    url: str | None
    category: str | None
    location: str | None
