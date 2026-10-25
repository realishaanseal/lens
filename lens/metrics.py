"""Mention rate, competitor counts and trends, computed from stored results.

Mention rate = prompts where the brand appears / prompts answered, per AI tool
and per month. When a prompt was checked more than once in a month, only the
latest answer counts; failed calls are excluded.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .store import Store

_LATEST = """
WITH ranked AS (
    SELECT r.*, ROW_NUMBER() OVER (
        PARTITION BY r.period, r.provider, r.prompt_id ORDER BY r.id DESC) AS rn
    FROM results r
    WHERE r.client_id = ? AND r.error IS NULL {where}
)
SELECT * FROM ranked WHERE rn = 1
"""


def latest_results(store: Store, client_id: str, period: str | None = None, provider: str | None = None) -> list[dict]:
    where, params = "", [client_id]
    if period:
        where += " AND r.period = ?"
        params.append(period)
    if provider:
        where += " AND r.provider = ?"
        params.append(provider)
    rows = store.query(_LATEST.format(where=where), tuple(params))
    results = [dict(row) for row in rows]
    if results:
        ids = [r["id"] for r in results]
        comps: dict[int, list[dict]] = {}
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            marks = ",".join("?" * len(chunk))
            for row in store.query(f"SELECT * FROM competitors WHERE result_id IN ({marks})", tuple(chunk)):
                comps.setdefault(row["result_id"], []).append({"name": row["name"], "kind": row["kind"]})
        for r in results:
            r["competitors"] = comps.get(r["id"], [])
    return results


def periods(store: Store, client_id: str) -> list[str]:
    rows = store.query("SELECT DISTINCT period FROM results WHERE client_id = ? ORDER BY period", (client_id,))
    return [row["period"] for row in rows]


def rate(results: list[dict]) -> float | None:
    return sum(r["mentioned"] for r in results) / len(results) if results else None


def _group_rate(results: list[dict], key: str) -> dict[str, float]:
    groups: dict[str, list[dict]] = {}
    for r in results:
        groups.setdefault(r[key] or "—", []).append(r)
    return {k: rate(v) for k, v in sorted(groups.items())}


def competitor_counts(results: list[dict]) -> list[tuple[str, int, float]]:
    """(name, answers naming it, share of answers), most frequent first."""
    counts = Counter()
    for r in results:
        for name in {c["name"] for c in r["competitors"]}:
            counts[name] += 1
    total = len(results) or 1
    return [(name, n, n / total) for name, n in counts.most_common()]


def traffic(store: Store, client_id: str, period: str | None = None) -> dict[str, dict[str, float]]:
    """{period: {"ga4.ai_assistant_users": 9, ...}}"""
    sql, params = "SELECT * FROM traffic WHERE client_id = ?", [client_id]
    if period:
        sql += " AND period = ?"
        params.append(period)
    out: dict[str, dict[str, float]] = {}
    for row in store.query(sql + " ORDER BY period", tuple(params)):
        out.setdefault(row["period"], {})[f"{row['source']}.{row['metric']}"] = row["value"]
    return out


@dataclass
class Summary:
    period: str
    mention_rate: float | None
    prompts_tested: int
    answers: int
    mentioned: int
    errors: int
    by_provider: dict[str, float] = field(default_factory=dict)
    by_language: dict[str, float] = field(default_factory=dict)
    top_competitors: list[tuple[str, int, float]] = field(default_factory=list)
    ai_visits: float | None = None
    previous_rate: float | None = None

    @property
    def top_competitor(self) -> str | None:
        return self.top_competitors[0][0] if self.top_competitors else None

    @property
    def change(self) -> float | None:
        if self.mention_rate is None or self.previous_rate is None:
            return None
        return self.mention_rate - self.previous_rate


def summarize(store: Store, client_id: str, period: str) -> Summary:
    results = latest_results(store, client_id, period)
    errors = store.query(
        "SELECT COUNT(*) AS n FROM results WHERE client_id = ? AND period = ? AND error IS NOT NULL",
        (client_id, period),
    )[0]["n"]
    earlier = [p for p in periods(store, client_id) if p < period]
    previous = rate(latest_results(store, client_id, earlier[-1])) if earlier else None
    visits = traffic(store, client_id, period).get(period, {}).get("ga4.ai_assistant_users")
    return Summary(
        period=period,
        mention_rate=rate(results),
        prompts_tested=len({r["prompt_id"] for r in results}),
        answers=len(results),
        mentioned=sum(r["mentioned"] for r in results),
        errors=errors,
        by_provider=_group_rate(results, "provider"),
        by_language=_group_rate(results, "language"),
        top_competitors=competitor_counts(results),
        ai_visits=visits,
        previous_rate=previous,
    )


def trend(store: Store, client_id: str) -> list[dict]:
    """One row per month: overall mention rate plus one column per AI tool."""
    rows = []
    for period in periods(store, client_id):
        results = latest_results(store, client_id, period)
        if results:
            rows.append({"period": period, "overall": rate(results), **_group_rate(results, "provider")})
    return rows
