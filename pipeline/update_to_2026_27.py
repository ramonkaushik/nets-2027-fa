"""
Migrate DB to 2026-27:
  - Insert new players (Randle, Ellis, etc.) into players table
  - Load their 2025-26 stats from cached leaguedash data
  - Load carried-over contract amounts; flag new/re-signed contracts as unknown
  - Seed 2026-27 cap constants
"""

import json
import os
import time

from nba_api.stats.endpoints import CommonTeamRoster
from db.init_db import get_connection, init_db
from pipeline.cache import fetch_with_cache

SEASON_NEW = '2026-27'
SEASON_OLD = '2025-26'
TEAM_ID = 1610612751

# From the live 2026-27 roster fetch
NEW_PLAYER_IDS = {
    'Julius Randle':    203944,
    'Keon Ellis':       1631165,
    'Mikel Brown Jr.':  1643414,
    'Joshua Jefferson': 1643538,
    'Tyler Bilodeau':   1643548,
}

# Contracts for players whose multi-year deals carry into 2026-27.
# Salaries are year-2 (or later) values from original deal.
# Rookie scale years escalate ~8%/yr; veteran deals flat unless structured.
CARRIED_CONTRACTS = {
    'Michael Porter Jr.': {'salary': 35417606, 'years_left': 0, 'option_type': 'none',  'guaranteed': 35417606},
    'Terance Mann':        {'salary': 14000000, 'years_left': 0, 'option_type': 'none',  'guaranteed': 14000000},
    'Noah Clowney':        {'salary':  7806600, 'years_left': 0, 'option_type': 'none',  'guaranteed':  7806600},
    "Day'Ron Sharpe":      {'salary':  7700000, 'years_left': 0, 'option_type': 'none',  'guaranteed':  7700000},
    'Egor Demin':          {'salary': 10555833, 'years_left': 2, 'option_type': 'team',  'guaranteed': 10555833},
    'Nolan Traore':        {'salary':  9044395, 'years_left': 2, 'option_type': 'team',  'guaranteed':  9044395},
    'Drake Powell':        {'salary':  7074302, 'years_left': 2, 'option_type': 'team',  'guaranteed':  7074302},
    'Danny Wolf':          {'salary':  2393066, 'years_left': 1, 'option_type': 'team',  'guaranteed':  2393066},
    'Ben Saraf':           {'salary':  2393066, 'years_left': 1, 'option_type': 'team',  'guaranteed':  2393066},
}

# 2026-27 cap constants (estimated — verify against NBPA/league memo)
CAP_CONSTANTS_2026_27 = {
    'salary_cap':    148000000,
    'tax_line':      180500000,
    'first_apron':   187600000,
    'second_apron':  198400000,
}


def _load_cached_leaguedash(season: str, measure: str) -> dict[int, dict]:
    path = os.path.join('data', 'cache', f'leaguedash_{measure}_{season}.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        rows = json.load(f)
    return {int(r['PLAYER_ID']): r for r in rows}


def run():
    init_db()
    conn = get_connection()

    # --- fetch 2026-27 roster ---
    def _fetch_roster():
        time.sleep(1)
        r = CommonTeamRoster(team_id=TEAM_ID, season=SEASON_NEW)
        return r.get_data_frames()[0].to_dict(orient='records')

    roster = fetch_with_cache(f'roster_BKN_{SEASON_NEW}', _fetch_roster)
    print(f"2026-27 roster: {len(roster)} players")

    # --- upsert all roster players ---
    for p in roster:
        exp = p.get('EXP')
        conn.execute(
            """
            INSERT INTO players (id, name, position, age, years_of_service)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, position=excluded.position,
                age=excluded.age, years_of_service=excluded.years_of_service
            """,
            (
                int(p['PLAYER_ID']), p['PLAYER'], p.get('POSITION'),
                p.get('AGE'), 0 if exp == 'R' else (int(exp) if exp else None),
            ),
        )

    # --- load 2025-26 stats for new additions ---
    base_idx = _load_cached_leaguedash(SEASON_OLD, 'Base')
    adv_idx  = _load_cached_leaguedash(SEASON_OLD, 'Advanced')

    new_ids = set(NEW_PLAYER_IDS.values())
    stats_loaded, stats_missing = [], []

    for name, nba_id in NEW_PLAYER_IDS.items():
        base = base_idx.get(nba_id)
        adv  = adv_idx.get(nba_id)
        if base is None:
            stats_missing.append(name)
            continue

        def f(d, k):
            try: return float(d[k])
            except: return None

        conn.execute(
            """
            INSERT INTO stats (
                player_id, season, gp, mpg, pts, reb, ast, stl, blk, tov,
                fg_pct, three_pct, three_pa, ft_pct,
                ts_pct, efg_pct, usg_pct, pts_per_75, per, bpm, vorp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id, season) DO NOTHING
            """,
            (
                nba_id, SEASON_OLD,
                base.get('GP'), f(base,'MIN'), f(base,'PTS'), f(base,'REB'), f(base,'AST'),
                f(base,'STL'), f(base,'BLK'), f(base,'TOV'),
                f(base,'FG_PCT'), f(base,'FG3_PCT'), f(base,'FG3A'), f(base,'FT_PCT'),
                f(adv,'TS_PCT') if adv else None,
                f(adv,'EFG_PCT') if adv else None,
                f(adv,'USG_PCT') if adv else None,
                None, None, None, None,
            ),
        )
        stats_loaded.append(name)

    print(f"2025-26 stats loaded for new players: {stats_loaded}")
    if stats_missing:
        print(f"No 2025-26 stats found for: {stats_missing} (rookies / overseas)")

    # --- seed cap constants ---
    cc = CAP_CONSTANTS_2026_27
    conn.execute(
        """
        INSERT INTO cap_constants (season, salary_cap, tax_line, first_apron, second_apron)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(season) DO UPDATE SET
            salary_cap=excluded.salary_cap, tax_line=excluded.tax_line,
            first_apron=excluded.first_apron, second_apron=excluded.second_apron
        """,
        (SEASON_NEW, cc['salary_cap'], cc['tax_line'], cc['first_apron'], cc['second_apron']),
    )

    # --- build name → id map ---
    db_players = conn.execute("SELECT id, name FROM players").fetchall()
    import re, unicodedata
    def norm(n):
        nfkd = unicodedata.normalize('NFKD', str(n))
        a = nfkd.encode('ascii','ignore').decode()
        a = re.sub(r'\b(jr|sr|ii|iii|iv)\.?', '', a, flags=re.IGNORECASE)
        return ' '.join(a.lower().split())
    name_to_id = {norm(p['name']): p['id'] for p in db_players}

    # --- load carried-over contracts ---
    unknown_contracts = []
    for p in roster:
        pname = p['PLAYER']
        key   = norm(pname)
        pid   = name_to_id.get(key)
        if pid is None:
            continue

        carried = CARRIED_CONTRACTS.get(pname) or CARRIED_CONTRACTS.get(norm(pname))
        # also check Demin alias
        if carried is None and 'demin' in key:
            carried = CARRIED_CONTRACTS.get('Egor Demin')

        if carried:
            conn.execute(
                """
                INSERT INTO contracts (player_id, season, salary, years_left, option_type, guaranteed)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id, season) DO UPDATE SET
                    salary=excluded.salary, years_left=excluded.years_left,
                    option_type=excluded.option_type, guaranteed=excluded.guaranteed
                """,
                (pid, SEASON_NEW, carried['salary'], carried['years_left'],
                 carried['option_type'], carried['guaranteed']),
            )
        else:
            unknown_contracts.append(pname)

    conn.commit()
    conn.close()

    print(f"\nContracts with unknown 2026-27 value (new signings / re-signed expirings):")
    for name in unknown_contracts:
        print(f"  {name}")
    print("\nRun cap_math.py --season 2026-27 once you fill those in.")


if __name__ == '__main__':
    run()
