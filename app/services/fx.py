from __future__ import annotations

import os
import time
from typing import Optional

import httpx

ENABLE_FX = os.getenv("ENABLE_FX", "true").lower() == "true"

_cache: dict[tuple[str, str], tuple[float, float]] = {}
# (from,to) -> (rate, exp)


def convert(amount: float, from_ccy: str, to_ccy: str) -> Optional[float]:
    from_ccy = from_ccy.upper()
    to_ccy = to_ccy.upper()

    if from_ccy == to_ccy:
        return amount

    if not ENABLE_FX:
        return None

    rate = _get_rate(from_ccy, to_ccy)
    if rate is None:
        return None
    return amount * rate


def _get_rate(from_ccy: str, to_ccy: str) -> Optional[float]:
    key = (from_ccy, to_ccy)
    now = time.time()

    if key in _cache and now < _cache[key][1]:
        return _cache[key][0]

    # Free endpoint (no key). If you prefer to avoid external FX calls, set ENABLE_FX=false.
    url = "https://api.exchangerate.host/convert"
    params = {"from": from_ccy, "to": to_ccy, "amount": 1}

    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            j = r.json()
            rate = float(j.get("result"))
    except Exception:
        return None

    _cache[key] = (rate, now + 60 * 60 * 6)  # 6 hours
    return rate
