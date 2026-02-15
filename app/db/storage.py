from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Optional

from dotenv import load_dotenv

from app.api.schemas import PriceRequest, PriceResponse

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/pricing.sqlite")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))


class Storage:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              query TEXT NOT NULL,
              fetched_at INTEGER NOT NULL,
              json TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
              key TEXT PRIMARY KEY,
              created_at INTEGER NOT NULL,
              response_json TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def cache_key(self, req: PriceRequest) -> str:
        # stable key for caching
        parts = {
            "q": req.query.strip().lower(),
            "condition": req.condition,
            "sold": req.sold,
            "currency": req.currency.upper(),
        }
        return json.dumps(parts, sort_keys=True)

    def get_cached_result(self, req: PriceRequest) -> Optional[PriceResponse]:
        key = self.cache_key(req)
        row = self.conn.execute("SELECT created_at, response_json FROM cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        if int(time.time()) - int(row["created_at"]) > CACHE_TTL_SECONDS:
            # expired
            self.conn.execute("DELETE FROM cache WHERE key=?", (key,))
            self.conn.commit()
            return None
        data = json.loads(row["response_json"])
        return PriceResponse(**data)

    def set_cached_result(self, req: PriceRequest, res: PriceResponse) -> None:
        key = self.cache_key(req)
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (key, created_at, response_json) VALUES (?, ?, ?)",
            (key, int(time.time()), res.model_dump_json()),
        )
        self.conn.commit()

    def save_raw_listings(self, query: str, raw_listings: list[dict]) -> None:
        self.conn.execute(
            "INSERT INTO listings (query, fetched_at, json) VALUES (?, ?, ?)",
            (query.strip().lower(), int(time.time()), json.dumps(raw_listings)),
        )
        self.conn.commit()
