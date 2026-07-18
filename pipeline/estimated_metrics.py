"""
Load E_OFF_RATING, E_DEF_RATING, E_NET_RATING from NBA.com PlayerEstimatedMetrics.
These are lineup-adjusted estimated impact ratings — closer to DARKO/EPM in concept
than box-score BPM, and come straight from the official NBA data source.

Works for any season and any set of player IDs already in the stats table.
"""

import time
from nba_api.stats.endpoints import PlayerEstimatedMetrics
from db.init_db import get_connection
from pipeline.cache import fetch_with_cache


def fetch_estimated_metrics(season: str) -> dict[int, dict]:
    key = f'estimated_metrics_{season}'

    def _fetch():
        time.sleep(1)
        r = PlayerEstimatedMetrics(season=season, season_type='Regular Season')
        df = r.get_data_frames()[0]
        return df[['PLAYER_ID', 'E_OFF_RATING', 'E_DEF_RATING', 'E_NET_RATING']].to_dict(orient='records')

    rows = fetch_with_cache(key, _fetch)
    return {int(r['PLAYER_ID']): r for r in rows}


def load_estimated_metrics(season: str, player_ids=None):
    """
    Update e_off_rating / e_def_rating / e_net_rating in the stats table.
    If player_ids is None, update all players who have a stats row for this season.
    """
    print(f"Fetching estimated metrics for {season}...")
    idx = fetch_estimated_metrics(season)

    conn = get_connection()
    if player_ids is None:
        rows = conn.execute(
            "SELECT player_id FROM stats WHERE season=?", (season,)
        ).fetchall()
        player_ids = {r['player_id'] for r in rows}

    updated, missing = 0, []
    for pid in player_ids:
        row = idx.get(pid)
        if row is None:
            missing.append(pid)
            continue
        conn.execute(
            """
            UPDATE stats SET e_off_rating=?, e_def_rating=?, e_net_rating=?
            WHERE player_id=? AND season=?
            """,
            (row['E_OFF_RATING'], row['E_DEF_RATING'], row['E_NET_RATING'], pid, season),
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f"Estimated metrics updated: {updated}/{len(player_ids)} players.")
    if missing:
        print(f"No estimated metrics for player IDs: {missing}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--season', default='2025-26')
    args = p.parse_args()
    load_estimated_metrics(args.season)
