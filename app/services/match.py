from __future__ import annotations

from rapidfuzz import fuzz

from app.services.normalize import title_keywords


def rank_and_filter(query: str, listings: list[dict], condition: str | None = None) -> list[dict]:
    qk = set(title_keywords(query))

    comps: list[dict] = []
    for l in listings:
        if condition and l.get("condition") != condition:
            continue

        lk = set(l.get("keywords") or [])
        overlap = 0.0
        if qk and lk:
            overlap = len(qk.intersection(lk)) / max(1, len(qk))

        # Fuzzy title match (0..100)
        ratio = fuzz.token_set_ratio(query.lower(), l["title"].lower()) / 100.0

        # Penalize obvious non-matches
        bad_words = {"proxy", "replica", "case", "cover", "empty box", "for parts"}
        title_l = l["title"].lower()
        if any(w in title_l for w in bad_words):
            ratio *= 0.6

        score = 0.55 * ratio + 0.45 * overlap
        if score < 0.35:
            continue

        x = dict(l)
        x["similarity"] = float(score)
        comps.append(x)

    comps.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    return comps[:120]
