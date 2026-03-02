# Pricing Intelligence Bot

> Very much a WIP cuz i'm ahh at Python

A self-hostable pricing engine for marketplace listings.

## What it does
Given a query (e.g. “Nintendo Switch OLED”), it:
1) pulls comparable listings (eBay Browse API)
2) normalizes fields (currency, condition buckets, duplicate/outlier removal)
3) matches similar items (keyword overlap + fuzzy similarity)
4) returns a recommended price (median) and a fair range (IQR)
5) caches results in SQLite for 12–24 hours

## Features
- FastAPI API
  - `GET /health`
  - `GET /price?q=...&condition=...&sold=false&currency=AED`
  - `POST /price` (richer inputs)
  - `GET /comps?q=...` (top comparable listings)
- eBay Browse API integration (official API)
- Condition standardization: `new | like_new | good | fair | unknown`
- Outlier removal (IQR)
- Confidence score (0–1) based on sample size + similarity + spread + recency
- SQLite storage
  - raw listings
  - cached query results

## Limitations (important)
- **Sold listings:** eBay Browse API does not provide sold/completed items. The API accepts `sold=true` for future support, but currently returns a clear error unless you implement eBay Marketplace Insights / other sold-data source.

## Quickstart (local)

### 1) Create an eBay developer app
Get:
- `EBAY_CLIENT_ID`
- `EBAY_CLIENT_SECRET`

### 2) Configure env

```bash
cp .env.example .env
```

### 3) Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- API docs: http://127.0.0.1:8000/docs

## Docker

```bash
docker compose up --build
```

## Example request

```bash
curl "http://127.0.0.1:8000/price?q=Nintendo%20Switch%20OLED&condition=good&sold=false&currency=AED"
```

## Repo structure

```
pricing-bot/
  app/
    main.py
    api/
      routes.py
      schemas.py
    services/
      ebay_client.py
      normalize.py
      match.py
      pricing.py
      fx.py
    db/
      storage.py
      models.py
  tests/
  scripts/
```

## Deploy notes
- Set env vars on your host
- Persist `./data/` volume for SQLite

