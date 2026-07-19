"""
Scrape Basketball Reference for PER, BPM, VORP, and pts_per_75 (from per-100
possessions table, scaled by 0.75).

Matches by normalized player name; flags any roster player that can't be
resolved rather than silently dropping them.
"""

import io
import time

import pandas as pd
import requests

from db.init_db import get_connection
from pipeline.cache import fetch_with_cache
from pipeline.utils import normalize_name

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

# BRef year = season end year: 2025-26 → 2026
BREF_YEAR = {
    '2025-26': 2026,
    '2024-25': 2025,
    '2023-24': 2024,
}

# Manual overrides for BRef names that don't ASCII-normalize cleanly.
# Key = BRef raw name, Value = normalized target to match against our DB.
NAME_OVERRIDES = {
    # Cyrillic ё has no ASCII equivalent — NFKD strips it entirely, turning
    # "Dёmin" into "dmin". Override before normalization runs.
    'Egor Dёmin': 'egor demin',
}


def _bref_url(year: int, table: str) -> str:
    return f"https://www.basketball-reference.com/leagues/NBA_{year}_{table}.html"


def _normalize(name: str) -> str:
    # Check manual overrides before running normalization — some names have
    # characters (e.g. Cyrillic ё) that don't survive ASCII conversion cleanly.
    return NAME_OVERRIDES.get(name) or normalize_name(name)


def _fetch_bref_table(url: str, cache_key: str) -> pd.DataFrame:
    def _get():
        time.sleep(3)  # BRef's ToS asks for a 3-second delay between requests
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        r.encoding = 'utf-8'
        dfs = pd.read_html(io.StringIO(r.text))
        return dfs[0].to_dict(orient='records')

    raw = fetch_with_cache(cache_key, _get)
    df = pd.DataFrame(raw)
    # BRef repeats the header row every 20 rows in the HTML table as a visual
    # aid — those rows land in the DataFrame with 'Player' == 'Player'.
    df = df[df['Player'] != 'Player'].copy()
    return df


def _dedup_traded_players(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the TOT row for players who were traded mid-season."""
    tot = df[df['Team'] == 'TOT']['Player'].unique()
    df = df[~((df['Player'].isin(tot)) & (df['Team'] != 'TOT'))]
    return df.copy()


def load_bref_stats(season: str):
    year = BREF_YEAR.get(season)
    if year is None:
        raise ValueError(f"No BRef year mapping for season {season!r}")

    print(f"Fetching BRef advanced stats for {season}...")
    adv_df = _fetch_bref_table(
        _bref_url(year, 'advanced'),
        f"bref_advanced_{season}",
    )
    adv_df = _dedup_traded_players(adv_df)

    print(f"Fetching BRef per-100-possessions stats for {season}...")
    per100_df = _fetch_bref_table(
        _bref_url(year, 'per_poss'),
        f"bref_per100_{season}",
    )
    per100_df = _dedup_traded_players(per100_df)

    # Build lookup: normalized_name → row
    adv_idx = {_normalize(r['Player']): r for r in adv_df.to_dict(orient='records')}
    per100_idx = {_normalize(r['Player']): r for r in per100_df.to_dict(orient='records')}

    conn = get_connection()
    roster = conn.execute(
        "SELECT id, name FROM players"
    ).fetchall()

    unmatched = []

    for player in roster:
        nba_id = player['id']
        nba_name = player['name']
        key = _normalize(nba_name)

        adv = adv_idx.get(key)
        per100 = per100_idx.get(key)

        if adv is None and per100 is None:
            unmatched.append(nba_name)
            continue

        def _float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        per_val = _float(adv.get('PER')) if adv else None
        bpm_val = _float(adv.get('BPM')) if adv else None
        vorp_val = _float(adv.get('VORP')) if adv else None
        pts100 = _float(per100.get('PTS')) if per100 else None
        # BRef's per-100 table = stats per 100 team possessions.
        # 75 possessions is a typical player's individual share per game,
        # so pts_per_75 is a more intuitive "points per game if usage were average".
        pts_per_75 = round(pts100 * 0.75, 2) if pts100 is not None else None

        conn.execute(
            """
            UPDATE stats
            SET per=?, bpm=?, vorp=?, pts_per_75=?
            WHERE player_id=? AND season=?
            """,
            (per_val, bpm_val, vorp_val, pts_per_75, nba_id, season),
        )

    conn.commit()
    conn.close()

    matched = len(roster) - len(unmatched)
    print(f"BRef stats updated: {matched}/{len(roster)} players.")
    if unmatched:
        print(f"UNMATCHED — BRef stats not updated for: {', '.join(unmatched)}")
    else:
        print("All players matched cleanly.")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--season', default='2025-26')
    args = p.parse_args()
    load_bref_stats(args.season)
