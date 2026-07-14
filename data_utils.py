"""Validated, cached analytics for the sales-performance dataset."""

import json
import os
from collections import defaultdict
from functools import lru_cache
from statistics import mean
from typing import Any

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sales_data.json")
MAX_PAGE_SIZE = 100
REQUIRED_FIELDS = {
    "id", "employee_code", "name", "region", "city", "manager", "product",
    "channel", "target", "achieved",
}


def _validate(data: dict[str, Any]) -> None:
    records = data.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("sales_data.json must contain a non-empty records list")
    if data.get("record_count") != len(records):
        raise ValueError("record_count does not match the number of records")

    seen_ids: set[int] = set()
    for position, record in enumerate(records, start=1):
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            raise ValueError(f"record {position} is missing: {', '.join(sorted(missing))}")
        if record["id"] in seen_ids:
            raise ValueError(f"duplicate record id: {record['id']}")
        seen_ids.add(record["id"])
        if record["target"] < 0 or record["achieved"] < 0:
            raise ValueError(f"record {record['id']} has a negative sales value")


@lru_cache(maxsize=2)
def _load_cached(modified_at: float) -> dict[str, Any]:
    del modified_at  # The mtime is the cache key and invalidates stale data.
    with open(DATA_PATH, encoding="utf-8") as source:
        data = json.load(source)
    _validate(data)
    return data


def _load() -> dict[str, Any]:
    return _load_cached(os.path.getmtime(DATA_PATH))


def _with_metrics(record: dict[str, Any]) -> dict[str, Any]:
    target = record["target"]
    achieved = record["achieved"]
    return {
        **record,
        "achievement_pct": round((achieved / target) * 100, 1) if target else 0,
        "variance": achieved - target,
        "status": "reached" if achieved >= target else "missed",
    }


def _all_records() -> list[dict[str, Any]]:
    return [_with_metrics(record) for record in _load()["records"]]


def _filtered_records(
    region: str | None = None,
    product: str | None = None,
    channel: str | None = None,
) -> list[dict[str, Any]]:
    filters = {"region": region, "product": product, "channel": channel}
    return [
        record for record in _all_records()
        if all(not value or record[key].casefold() == value.strip().casefold()
               for key, value in filters.items())
    ]


def _page(records: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    page = max(1, page)
    page_size = min(MAX_PAGE_SIZE, max(1, page_size))
    start = (page - 1) * page_size
    return {
        "items": records[start:start + page_size],
        "page": page,
        "page_size": page_size,
        "total": len(records),
        "total_pages": (len(records) + page_size - 1) // page_size,
    }


def team_target_summary(
    region: str | None = None,
    product: str | None = None,
    channel: str | None = None,
) -> dict[str, Any]:
    """Overall target performance, optionally filtered by business dimensions."""
    data = _load()
    records = _filtered_records(region, product, channel)
    total_target = sum(record["target"] for record in records)
    total_achieved = sum(record["achieved"] for record in records)
    return {
        "month": data["month"],
        "team_name": data["team_name"],
        "record_count": len(records),
        "team_target": total_target,
        "team_achieved": total_achieved,
        "team_achievement_pct": round(total_achieved / total_target * 100, 1) if total_target else 0,
        "reps_who_reached_target": sum(record["status"] == "reached" for record in records),
        "filters": {k: v for k, v in {"region": region, "product": product, "channel": channel}.items() if v},
    }


def top_performer(n: int = 1, region: str | None = None) -> list[dict[str, Any]]:
    """Top performers by achievement percentage."""
    return sorted(_filtered_records(region=region), key=lambda r: r["achievement_pct"], reverse=True)[:max(1, min(n, 100))]


def bottom_performer(n: int = 1, region: str | None = None) -> list[dict[str, Any]]:
    """Lowest performers by achievement percentage."""
    return sorted(_filtered_records(region=region), key=lambda r: r["achievement_pct"])[:max(1, min(n, 100))]


def average_performer() -> dict[str, Any]:
    """Team averages and two representatives closest to the average."""
    records = _all_records()
    avg_pct = round(mean(record["achievement_pct"] for record in records), 1)
    return {
        "average_target": round(mean(record["target"] for record in records)),
        "average_achieved": round(mean(record["achieved"] for record in records)),
        "average_achievement_pct": avg_pct,
        "closest_to_average": sorted(records, key=lambda r: abs(r["achievement_pct"] - avg_pct))[:2],
    }


def performers_by_status(status: str, page: int = 1, page_size: int = 25) -> dict[str, Any]:
    """Paginated representatives who reached or missed target."""
    normalized = status.strip().casefold()
    if normalized not in {"reached", "missed"}:
        raise ValueError("status must be 'reached' or 'missed'")
    records = [record for record in _all_records() if record["status"] == normalized]
    records.sort(key=lambda r: r["achievement_pct"], reverse=normalized == "reached")
    return _page(records, page, page_size)


def who_reached_target(page: int = 1, page_size: int = 25) -> dict[str, Any]:
    return performers_by_status("reached", page, page_size)


def who_missed_target(page: int = 1, page_size: int = 25) -> dict[str, Any]:
    return performers_by_status("missed", page, page_size)


def individual_performance(query: str, page: int = 1, page_size: int = 25) -> dict[str, Any]:
    """Find representatives by name or exact employee code."""
    term = query.strip().casefold()
    matches = [
        record for record in _all_records()
        if term in record["name"].casefold() or term == record["employee_code"].casefold()
    ]
    return _page(matches, page, page_size)


def dimension_breakdown(dimension: str = "region") -> dict[str, dict[str, Any]]:
    """Roll up target performance by region, product, channel, city, or manager."""
    if dimension not in {"region", "product", "channel", "city", "manager"}:
        raise ValueError("unsupported dimension")
    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {"target": 0, "achieved": 0, "reps": 0})
    for record in _all_records():
        group = groups[record[dimension]]
        group["target"] += record["target"]
        group["achieved"] += record["achieved"]
        group["reps"] += 1
    for group in groups.values():
        group["achievement_pct"] = round(group["achieved"] / group["target"] * 100, 1) if group["target"] else 0
    return dict(sorted(groups.items()))


def region_breakdown() -> dict[str, dict[str, Any]]:
    return dimension_breakdown("region")


def full_leaderboard(page: int = 1, page_size: int = 25) -> dict[str, Any]:
    """Paginated leaderboard ranked best to worst."""
    records = sorted(_all_records(), key=lambda r: r["achievement_pct"], reverse=True)
    return _page(records, page, page_size)


if __name__ == "__main__":
    import pprint
    pprint.pprint(team_target_summary())
    pprint.pprint(dimension_breakdown("region"))
