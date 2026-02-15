from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional


ConditionBucket = Literal["new", "like_new", "good", "fair", "unknown"]


class PriceRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search query")
    condition: Optional[ConditionBucket] = Field(None, description="Condition bucket filter")
    sold: bool = Field(False, description="Use sold listings if supported")
    currency: str = Field("USD", description="Output currency")
    limit: int = Field(80, ge=10, le=200, description="Max listings to fetch")


class ComparableListing(BaseModel):
    title: str
    price: float
    currency: str
    shipping_cost: float = 0
    condition: ConditionBucket = "unknown"
    sold: bool = False
    date: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    similarity: float = 0


class PriceResponse(BaseModel):
    query: str
    condition: Optional[ConditionBucket]
    sold: bool
    currency: str
    suggested_price: float
    fair_range: tuple[float, float]
    confidence: float = Field(..., ge=0, le=1)
    sample_size: int
    top_comps: list[ComparableListing]
    notes: list[str] = []
