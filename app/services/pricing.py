from __future__ import annotations

import math
import statistics
import time
from typing import Iterable

from app.api.schemas import ComparableListing, PriceRequest, PriceResponse


def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float('nan')
    n = len(sorted_vals)
    idx = (n - 1) * q
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (idx - lo)


def remove_outliers_iqr(vals: list[float]) -> list[float]:
    if len(vals) < 8:
        return vals
    s = sorted(vals)
    q1 = _quantile(s, 0.25)
    q3 = _quantile(s, 0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return vals
    lo = q1 - 1.5 * iqr
    hi = q3 + 1.5 * iqr
    return [v for v in vals if lo <= v <= hi]


def confidence_score(comps: list[dict], vals: list[float]) -> float:
    n = len(vals)
    if n == 0:
        return 0.0

    # sample size factor
    size = 1 - math.exp(-n / 25)

    # similarity factor
    sim_avg = sum(c.get("similarity", 0) for c in comps[: min(30, len(comps))]) / max(1, min(30, len(comps)))

    # spread factor (tighter = better)
    s = sorted(vals)
    q1 = _quantile(s, 0.25)
    q3 = _quantile(s, 0.75)
    iqr = max(1e-6, q3 - q1)
    med = max(1e-6, _quantile(s, 0.5))
    spread = 1 - min(1.0, (iqr / med))

    # recency factor (we don't have listing dates from Browse; assume medium)
    recency = 0.6

    conf = 0.35 * size + 0.35 * sim_avg + 0.2 * spread + 0.1 * recency
    return float(max(0.0, min(1.0, conf)))


def price_from_comps(req: PriceRequest, comps: list[dict]) -> PriceResponse:
    notes: list[str] = []

    if not comps:
        raise ValueError("No comparable listings found")

    vals = [float(c["price"]) for c in comps if c.get("price") is not None]
    vals_clean = remove_outliers_iqr(vals)

    if len(vals_clean) < len(vals):
        notes.append(f"Removed {len(vals) - len(vals_clean)} outliers using IQR")

    s = sorted(vals_clean)
    median = statistics.median(s)
    q1 = _quantile(s, 0.25)
    q3 = _quantile(s, 0.75)

    conf = confidence_score(comps, vals_clean)

    top = [ComparableListing(**c).model_dump() for c in comps[:10]]

    return PriceResponse(
        query=req.query,
        condition=req.condition,
        sold=req.sold,
        currency=(s and req.currency.upper()) or "USD",
        suggested_price=float(round(median, 2)),
        fair_range=(float(round(q1, 2)), float(round(q3, 2))),
        confidence=float(round(conf, 2)),
        sample_size=len(vals_clean),
        top_comps=[ComparableListing(**c) for c in comps[:10]],
        notes=notes,
    )
