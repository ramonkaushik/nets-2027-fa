"""
Pull Brooklyn Nets roster + per-player stats for a given season via nba_api,
then load into SQLite. Caches all API responses to data/cache/.

Stats loaded:
  Basic (PerGame):  gp, mpg, pts, reb, ast, stl, blk, tov, fg_pct,
                    three_pct, three_pa, ft_pct
  Advanced:         ts_pct, efg_pct, usg_pct
  Not available via nba_api (set to NULL): pts_per_75, per, bpm, vorp

Usage:
  python -m pipeline.nets_stats [--season 2025-26]
"""

import argparse
import sys

from nba_api.stats.endpoints import CommonTeamRoster, LeagueDashPlayerStats
from nba_api.stats.static import teams

from db.init_db import get_connection, init_db
from pipeline.cache import fetch_with_cache

NETS_ABBREV = 'BKN'


def get_nets_team_id() -> int:
    nba_teams = teams.get_teams()
    nets = next(t for t in nba_teams if t['abbreviation'] == NETS_ABBREV)
    return nets['id']


def fetch_roster(team_id: int, season: str) -> list[dict]:
    key = f"roster_{NETS_ABBREV}_{season}"

    def _fetch():
        r = CommonTeamRoster(team_id=team_id, season=season)
        df = r.get_data_frames()[0]
        return df.to_dict(orient='records')

    return fetch_with_cache(key, _fetch)


def fetch_league_stats(season: str, measure_type: str) -> list[dict]:
    key = f"leaguedash_{measure_type}_{season}"

    def _fetch():
        # LeagueDashPlayerStats returns every player in the league — we filter
        # to Nets players afterwards using the player IDs from CommonTeamRoster.
        # The trailing zeros/N's are required boilerplate; the API rejects calls
        # that leave them out even though they're semantically "no filter".
        r = LeagueDashPlayerStats(
            season=season,
            measure_type_detailed_defense=measure_type,
            per_mode_detailed='PerGame',
            last_n_games=0,
            month=0,
            opponent_team_id=0,
            pace_adjust='N',
            period=0,
            plus_minus='N',
            rank='N',
            season_type_all_star='Regular Season',
        )
        df = r.get_data_frames()[0]
        return df.to_dict(orient='records')

    return fetch_with_cache(key, _fetch)


def build_stats_index(records: list[dict], id_col: str) -> dict[int, dict]:
    return {int(r[id_col]): r for r in records}


def load_season(season: str):
    init_db()
    conn = get_connection()

    team_id = get_nets_team_id()
    print(f"Brooklyn Nets team_id: {team_id}")

    # --- roster ---
    roster = fetch_roster(team_id, season)
    print(f"Roster entries fetched: {len(roster)}")

    # --- league-wide stats ---
    print("Fetching base per-game stats...")
    base_rows = fetch_league_stats(season, 'Base')
    print("Fetching advanced stats...")
    adv_rows = fetch_league_stats(season, 'Advanced')

    base_idx = build_stats_index(base_rows, 'PLAYER_ID')
    adv_idx = build_stats_index(adv_rows, 'PLAYER_ID')

    unmatched = []

    for player in roster:
        nba_id = int(player['PLAYER_ID'])
        name = player['PLAYER']
        position = player.get('POSITION', None)

        # upsert player row
        conn.execute(
            """
            INSERT INTO players (id, name, position, age, years_of_service)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                position=excluded.position,
                age=excluded.age,
                years_of_service=excluded.years_of_service
            """,
            (
                nba_id,
                name,
                position,
                player.get('AGE'),
                player.get('EXP') if player.get('EXP') != 'R' else 0,  # 'R' = rookie
            ),
        )

        base = base_idx.get(nba_id)
        adv = adv_idx.get(nba_id)

        if base is None or adv is None:
            unmatched.append({'id': nba_id, 'name': name, 'missing': [] +
                              (['base'] if base is None else []) +
                              (['advanced'] if adv is None else [])})
            continue

        conn.execute(
            """
            INSERT INTO stats (
                player_id, season,
                gp, mpg, pts, reb, ast, stl, blk, tov,
                fg_pct, three_pct, three_pa, ft_pct,
                ts_pct, efg_pct, usg_pct,
                pts_per_75, per, bpm, vorp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id, season) DO UPDATE SET
                gp=excluded.gp, mpg=excluded.mpg,
                pts=excluded.pts, reb=excluded.reb, ast=excluded.ast,
                stl=excluded.stl, blk=excluded.blk, tov=excluded.tov,
                fg_pct=excluded.fg_pct, three_pct=excluded.three_pct,
                three_pa=excluded.three_pa, ft_pct=excluded.ft_pct,
                ts_pct=excluded.ts_pct, efg_pct=excluded.efg_pct,
                usg_pct=excluded.usg_pct
            """,
            (
                nba_id, season,
                base.get('GP'), base.get('MIN'),   # MIN = avg minutes per game
                base.get('PTS'), base.get('REB'), base.get('AST'),
                base.get('STL'), base.get('BLK'), base.get('TOV'),
                base.get('FG_PCT'), base.get('FG3_PCT'), base.get('FG3A'),
                base.get('FT_PCT'),
                adv.get('TS_PCT'), adv.get('EFG_PCT'), adv.get('USG_PCT'),
                None, None, None, None,  # pts_per_75/per/bpm/vorp come from BRef scrape, not nba_api
            ),
        )

    conn.commit()
    conn.close()

    # --- report ---
    matched = len(roster) - len(unmatched)
    print(f"\nLoaded {matched}/{len(roster)} players into stats table for {season}.")

    if unmatched:
        print(f"\nUNMATCHED ({len(unmatched)}) — stats not loaded:")
        for p in unmatched:
            print(f"  [{p['id']}] {p['name']} — missing: {', '.join(p['missing'])}")
    else:
        print("All roster players resolved cleanly.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2025-26',
                        help='NBA season string, e.g. 2025-26')
    args = parser.parse_args()
    load_season(args.season)
