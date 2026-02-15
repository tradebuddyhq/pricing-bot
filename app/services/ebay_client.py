from __future__ import annotations

import base64
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")
EBAY_ENV = os.getenv("EBAY_ENV", "production")
EBAY_MARKETPLACE_ID = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US")

BASE = {
    "production": {
        "api": "https://api.ebay.com",
        "oauth": "https://api.ebay.com/identity/v1/oauth2/token",
    },
    "sandbox": {
        "api": "https://api.sandbox.ebay.com",
        "oauth": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
    },
}

SCOPE_BROWSE = "https://api.ebay.com/oauth/api_scope"


class EbayClient:
    def __init__(self):
        if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
            # We keep it lazy; endpoints will error with a helpful message.
            pass
        self._token: str | None = None
        self._token_exp: float = 0

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp - 30:
            return self._token

        if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
            raise RuntimeError("Missing EBAY_CLIENT_ID / EBAY_CLIENT_SECRET")

        basic = base64.b64encode(f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode("utf-8")).decode("utf-8")

        data = {
            "grant_type": "client_credentials",
            "scope": SCOPE_BROWSE,
        }

        with httpx.Client(timeout=20) as client:
            r = client.post(
                BASE[EBAY_ENV]["oauth"],
                data=data,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            r.raise_for_status()
            j = r.json()

        self._token = j["access_token"]
        self._token_exp = now + float(j.get("expires_in", 7200))
        return self._token

    def search_active(self, query: str, limit: int = 80) -> list[dict[str, Any]]:
        token = self._get_token()
        url = BASE[EBAY_ENV]["api"] + "/buy/browse/v1/item_summary/search"

        # eBay Browse uses limit/offset; we do 1 page for MVP.
        params = {
            "q": query,
            "limit": min(max(limit, 10), 200),
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": EBAY_MARKETPLACE_ID,
            "Accept": "application/json",
        }

        with httpx.Client(timeout=20) as client:
            r = client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()

        items = data.get("itemSummaries") or []

        out: list[dict[str, Any]] = []
        for it in items:
            out.append(
                {
                    "title": it.get("title"),
                    "price": (it.get("price") or {}).get("value"),
                    "currency": (it.get("price") or {}).get("currency"),
                    "shipping_cost": ((it.get("shippingOptions") or [{}])[0].get("shippingCost") or {}).get("value", 0),
                    "shipping_currency": ((it.get("shippingOptions") or [{}])[0].get("shippingCost") or {}).get("currency"),
                    "condition": it.get("condition"),
                    "sold": False,
                    "date": None,
                    "url": it.get("itemWebUrl"),
                    "category": (it.get("categories") or [{}])[0].get("categoryName"),
                    "location": (it.get("itemLocation") or {}).get("country"),
                }
            )

        return out
