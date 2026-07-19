import json
import os
import time

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache')


def _cache_path(key: str) -> str:
    safe = key.replace('/', '_').replace(' ', '_')
    return os.path.join(CACHE_DIR, f"{safe}.json")


def load(key: str):
    path = _cache_path(key)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save(key: str, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(key), 'w') as f:
        json.dump(data, f)


def fetch_with_cache(key: str, fetch_fn, delay: float = 1.0):
    # Skip the network entirely if we already have this response on disk.
    # NBA.com and BRef rate-limit aggressively; re-fetching on every run
    # risks getting blocked and wastes several seconds per call.
    cached = load(key)
    if cached is not None:
        return cached
    time.sleep(delay)  # be polite — space out requests before hitting the API
    data = fetch_fn()
    save(key, data)
    return data
