import json
import time
from pathlib import Path

import requests

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

NSF_BASE_URL = "https://api.nsf.gov/services/v1/awards.json"


def fetch_nsf_grants(pi_name: str) -> list[dict]:
    """
    Fetches active NSF grants for a PI by last name.
    Filters to grants expiring on or after 2024.

    Returns list of Grant dicts:
        [{title, amount, expiry_date, citizen_only}]

    citizen_only is never set by the NSF API itself — it defaults to False here.
    Override it manually in seed JSON when a grant has citizenship requirements.

    Caches to data/cache/nsf_{lastname}.json.
    """
    last_name = pi_name.strip().split()[-1].lower()
    cache_path = CACHE_DIR / f"nsf_{last_name}.json"

    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    params = {
        "pdPIName": last_name,
        "expDateStart": "01/01/2024",
        "printFields": (
            "id,title,awardeeName,piFirstName,piLastName,"
            "fundsObligatedAmt,expDate"
        ),
    }

    try:
        time.sleep(1)
        r = requests.get(NSF_BASE_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        raw_awards = data.get("response", {}).get("award", []) or []
    except Exception as e:
        print(f"NSF fetch failed for '{pi_name}': {e}")
        raw_awards = []

    grants = [
        {
            "id": a.get("id", ""),
            "title": a.get("title", ""),
            "awardee": a.get("awardeeName", ""),
            "pi_first": a.get("piFirstName", ""),
            "pi_last": a.get("piLastName", ""),
            "amount": _parse_amount(a.get("fundsObligatedAmt")),
            "expiry_date": a.get("expDate", ""),
            "citizen_only": False,  # set manually in seed JSON when needed
        }
        for a in raw_awards
    ]

    with open(cache_path, "w") as f:
        json.dump(grants, f, indent=2)

    return grants


def _parse_amount(raw) -> int:
    try:
        return int(str(raw).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    # Quick smoke test
    grants = fetch_nsf_grants("Pachter")
    print(f"Found {len(grants)} NSF awards for Pachter")
    for g in grants[:3]:
        print(f"  ${g['amount']:,} | {g['expiry_date']} | {g['title'][:60]}")
