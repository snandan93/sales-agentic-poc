"""Generate a deterministic, realistic sales-performance dataset."""

import json
import random
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "sales_data.json"
RECORD_COUNT = 1_000
SEED = 202607

FIRST_NAMES = [
    "Aarav", "Aditi", "Aditya", "Akash", "Ananya", "Anjali", "Arjun", "Deepak",
    "Divya", "Farhan", "Ishita", "Karan", "Kavya", "Meera", "Neha", "Nikhil",
    "Pooja", "Priya", "Rahul", "Rajesh", "Riya", "Rohit", "Sana", "Sneha",
    "Suresh", "Tanvi", "Varun", "Vikram", "Vivek", "Zoya",
]
LAST_NAMES = [
    "Bose", "Chandra", "Chopra", "Das", "Desai", "Gupta", "Iyer", "Jain",
    "Joshi", "Kapoor", "Khan", "Kumar", "Mehta", "Menon", "Mishra", "Nair",
    "Patel", "Pillai", "Rao", "Reddy", "Shah", "Sharma", "Singh", "Verma",
]
REGIONS = {
    "North": ["Delhi", "Jaipur", "Chandigarh", "Lucknow"],
    "South": ["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
    "East": ["Kolkata", "Bhubaneswar", "Guwahati", "Patna"],
    "West": ["Mumbai", "Pune", "Ahmedabad", "Goa"],
    "Central": ["Bhopal", "Indore", "Nagpur", "Raipur"],
}
PRODUCTS = ["CRM Suite", "Analytics Pro", "Support Cloud", "Commerce Hub"]
CHANNELS = ["Direct", "Partner", "Inside Sales"]


def generate_records(count: int = RECORD_COUNT, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    records = []
    regions = list(REGIONS)
    for index in range(1, count + 1):
        region = regions[(index - 1) % len(regions)]
        first = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
        last = LAST_NAMES[((index - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]
        name = f"{first} {last} {index:04d}"
        target = rng.randrange(300_000, 800_001, 10_000)
        performance_factor = min(1.55, max(0.45, rng.normalvariate(0.98, 0.20)))
        achieved = round(target * performance_factor / 1_000) * 1_000
        records.append(
            {
                "id": index,
                "employee_code": f"SR-{index:04d}",
                "name": name,
                "region": region,
                "city": rng.choice(REGIONS[region]),
                "manager": f"Manager {region}",
                "product": rng.choice(PRODUCTS),
                "channel": rng.choice(CHANNELS),
                "target": target,
                "achieved": achieved,
            }
        )
    return records


def main() -> None:
    payload = {
        "schema_version": 2,
        "month": "July 2026",
        "team_name": "India Field Sales Team",
        "generated_on": "2026-07-14",
        "record_count": RECORD_COUNT,
        "records": generate_records(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {RECORD_COUNT} records at {OUTPUT}")


if __name__ == "__main__":
    main()
