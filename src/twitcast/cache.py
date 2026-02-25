"""Generic JSON file cache with TTL."""

import json
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)


def read_cache(path: Path, max_age_hours: float) -> dict | None:
    """Read cached JSON if it exists and is fresh enough.

    Returns the parsed dict or None if stale/missing/corrupt.
    """
    if not path.exists():
        return None
    try:
        with open(path) as f:
            cached = json.load(f)
        hours_since = (time.time() - cached["timestamp"]) / 3600
        if hours_since < max_age_hours:
            log.info("Using cache %s (%.1fh old)", path.name, hours_since)
            return cached
    except (json.JSONDecodeError, KeyError, OSError) as e:
        log.warning("Corrupt cache %s, ignoring: %s", path.name, e)
    return None


def write_cache(path: Path, data: dict) -> None:
    """Write data dict to cache file with current timestamp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**data, "timestamp": time.time()}
    with open(path, "w") as f:
        json.dump(payload, f)
