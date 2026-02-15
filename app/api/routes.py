from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import PriceRequest, PriceResponse
from app.db.storage import Storage
from app.services.ebay_client import EbayClient
from app.services.normalize import normalize_listings
from app.services.match import rank_and_filter
from app.services.pricing import price_from_comps

router = APIRouter()

storage = Storage()
eb = EbayClient()


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/price", response_model=PriceResponse)
def get_price(
    q: str = Query(..., min_length=2),
    condition: str | None = Query(None),
    sold: bool = Query(False),
    currency: str = Query("USD"),
):
    req = PriceRequest(query=q, condition=condition, sold=sold, currency=currency)
    return compute_price(req)


@router.post("/price", response_model=PriceResponse)
def post_price(req: PriceRequest):
    return compute_price(req)


@router.get("/comps")
def get_comps(q: str = Query(..., min_length=2), currency: str = Query("USD"), limit: int = Query(10, ge=1, le=50)):
    req = PriceRequest(query=q, currency=currency)
    res = compute_price(req)
    return {"query": q, "currency": currency, "sample_size": res.sample_size, "top_comps": res.top_comps[:limit]}


def compute_price(req: PriceRequest) -> PriceResponse:
    if req.sold:
        raise HTTPException(
            status_code=400,
            detail="sold=true is not supported with eBay Browse API. Implement Marketplace Insights or another sold-data source first.",
        )

    # Cache
    cached = storage.get_cached_result(req)
    if cached:
        return cached

    raw = eb.search_active(query=req.query, limit=req.limit)
    storage.save_raw_listings(req.query, raw)

    normalized = normalize_listings(raw, out_currency=req.currency)
    comps = rank_and_filter(req.query, normalized, condition=req.condition)

    result = price_from_comps(req, comps)

    storage.set_cached_result(req, result)
    return result
