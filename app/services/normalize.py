from __future__ import annotations

import re
from typing import Any

from app.services.fx import convert


CONDITION_BUCKETS = {
    "new": "new",
    "brand new": "new",
    "new with tags": "new",
    "new with box": "new",
    "open box": "like_new",
    "like new": "like_new",
    "used": "good",
    "pre-owned": "good",
    "very good": "good",
    "good": "good",
    "acceptable": "fair",
    "fair": "fair",
    "for parts": "fair",
    "not working": "fair",
}


def normalize_condition(raw: str | None) -> str:
    if not raw:
        return "unknown"
    s = raw.strip().lower()
    for k, v in CONDITION_BUCKETS.items():
        if k in s:
            return v
    return "unknown"


def title_keywords(title: str) -> list[str]:
    # basic tokenization
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    toks = [x for x in t.split() if len(x) >= 2]
    # remove some noisy tokens
    stop = {"the", "and", "with", "for", "new", "free", "sale", "pack"}
    return [x for x in toks if x not in stop]


def normalize_listings(raw: list[dict[str, Any]], out_currency: str = "USD") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for r in raw:
        title = (r.get("title") or "").strip()
        if not title:
            continue

        try:
            price = float(r.get("price"))
        except Exception:
            continue

        currency = (r.get("currency") or "").upper() or out_currency

        ship_cost = 0.0
        try:
            ship_cost = float(r.get("shipping_cost") or 0)
        except Exception:
            ship_cost = 0.0

        ship_currency = (r.get("shipping_currency") or currency).upper()

        # Convert currency
        price_conv = convert(price, currency, out_currency)
        ship_conv = convert(ship_cost, ship_currency, out_currency)

        if price_conv is None:
            # fallback: keep original currency if FX disabled/unavailable
            out_ccy = currency
            total = price + ship_cost
        else:
            out_ccy = out_currency.upper()
            total = price_conv + (ship_conv or 0.0)

        out.append(
            {
                "title": title,
                "price": float(total),
                "currency": out_ccy,
                "shipping_cost": float(ship_conv or ship_cost),
                "condition": normalize_condition(r.get("condition")),
                "sold": bool(r.get("sold")),
                "date": r.get("date"),
                "url": r.get("url"),
                "category": r.get("category"),
                "location": r.get("location"),
                "keywords": title_keywords(title),
            }
        )

    # Remove duplicates by URL if present
    seen = set()
    dedup = []
    for x in out:
        key = x.get("url") or (x["title"].lower(), round(x["price"], 2))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(x)

    return dedup
