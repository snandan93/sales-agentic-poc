"""
data_utils.py
--------------
Pure Python analytics over the sales dataset. No MCP / LangChain / Ollama
imports here on purpose — this module is the "single source of truth" for
business logic, and mcp_server.py just exposes each function as a tool.
Keeping it separate also means it can be unit-tested with plain `python`.
"""

import json
import os
from statistics import mean

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sales_data.json")


def _load():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def _with_pct(rec):
    """Attach achievement % to a record."""
    pct = round((rec["achieved"] / rec["target"]) * 100, 1) if rec["target"] else 0
    return {**rec, "achievement_pct": pct}


def _all_records():
    return [_with_pct(r) for r in _load()["records"]]


def team_target_summary():
    """Overall team target vs. achieved for the month, with % completion."""
    data = _load()
    records = data["records"]
    total_target = sum(r["target"] for r in records)
    total_achieved = sum(r["achieved"] for r in records)
    pct = round((total_achieved / total_target) * 100, 1) if total_target else 0
    reached = sum(1 for r in records if r["achieved"] >= r["target"])
    return {
        "month": data["month"],
        "team_name": data["team_name"],
        "team_size": len(records),
        "team_target": total_target,
        "team_achieved": total_achieved,
        "team_achievement_pct": pct,
        "reps_who_reached_target": reached,
    }


def top_performer(n: int = 1):
    """Top N performers ranked by achievement % (achieved / target)."""
    ranked = sorted(_all_records(), key=lambda r: r["achievement_pct"], reverse=True)
    return ranked[:n]


def bottom_performer(n: int = 1):
    """Bottom N performers ranked by achievement % — useful for coaching focus."""
    ranked = sorted(_all_records(), key=lambda r: r["achievement_pct"])
    return ranked[:n]


def average_performer():
    """
    Team average stats, plus the rep(s) whose achievement % is closest to
    the team average (i.e. the 'typical'/average performer).
    """
    records = _all_records()
    avg_target = round(mean(r["target"] for r in records), 0)
    avg_achieved = round(mean(r["achieved"] for r in records), 0)
    avg_pct = round(mean(r["achievement_pct"] for r in records), 1)

    closest = sorted(records, key=lambda r: abs(r["achievement_pct"] - avg_pct))[:2]
    return {
        "average_target": avg_target,
        "average_achieved": avg_achieved,
        "average_achievement_pct": avg_pct,
        "closest_to_average": closest,
    }


def who_reached_target():
    """All reps whose achieved >= target this month, sorted by achievement %."""
    records = [r for r in _all_records() if r["achieved"] >= r["target"]]
    return sorted(records, key=lambda r: r["achievement_pct"], reverse=True)


def who_missed_target():
    """All reps who did not reach target this month, sorted worst-first."""
    records = [r for r in _all_records() if r["achieved"] < r["target"]]
    return sorted(records, key=lambda r: r["achievement_pct"])


def individual_performance(name: str):
    """Look up a single rep by name (case-insensitive, partial match ok)."""
    name_lower = name.lower().strip()
    matches = [r for r in _all_records() if name_lower in r["name"].lower()]
    return matches


def region_breakdown():
    """Target vs achieved rolled up by region — helps spot regional gaps."""
    records = _all_records()
    regions = {}
    for r in records:
        reg = r["region"]
        regions.setdefault(reg, {"target": 0, "achieved": 0, "reps": 0})
        regions[reg]["target"] += r["target"]
        regions[reg]["achieved"] += r["achieved"]
        regions[reg]["reps"] += 1
    for reg, v in regions.items():
        v["achievement_pct"] = round((v["achieved"] / v["target"]) * 100, 1) if v["target"] else 0
    return regions


def full_leaderboard():
    """Every rep, ranked best to worst by achievement %."""
    return sorted(_all_records(), key=lambda r: r["achievement_pct"], reverse=True)


if __name__ == "__main__":
    # Quick self-test — run with: python data_utils.py
    import pprint
    pprint.pprint(team_target_summary())
    print("\nTop performer:")
    pprint.pprint(top_performer())
    print("\nBottom performer:")
    pprint.pprint(bottom_performer())
    print("\nAverage performer:")
    pprint.pprint(average_performer())
    print("\nReached target count:", len(who_reached_target()))
    print("\nRegion breakdown:")
    pprint.pprint(region_breakdown())
