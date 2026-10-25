"""Imports GA4 and Search Console numbers so they sit next to AI mentions.

MVP input is a CSV export with the columns: period,source,metric,value
for example:  2026-10,ga4,ai_assistant_users,9
Sources are "ga4" or "gsc". Common metrics: ai_assistant_users, organic_users,
clicks, impressions.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .store import Store

_PERIOD = re.compile(r"^\d{4}-\d{2}$")


def import_csv(store: Store, client_id: str, path: str | Path) -> int:
    count = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for line, row in enumerate(csv.DictReader(fh), start=2):
            try:
                period = row["period"].strip()
                source = row["source"].strip().lower()
                metric = row["metric"].strip()
                value = float(row["value"])
            except (KeyError, ValueError, AttributeError) as exc:
                raise ValueError(f"{path}:{line}: expected period,source,metric,value") from exc
            if not _PERIOD.match(period):
                raise ValueError(f"{path}:{line}: period must look like 2026-10")
            if source not in ("ga4", "gsc"):
                raise ValueError(f"{path}:{line}: source must be ga4 or gsc")
            store.set_traffic(client_id, period, source, metric, value)
            count += 1
    return count
