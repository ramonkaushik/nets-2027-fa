"""
Build the 2027 free agent pool:
  1. Scrape Spotrac for all 2027 UFAs/RFAs (191 players)
  2. Match to NBA player IDs via nba_api player lookup
  3. Load 2025-26 stats from cached leaguedash data
  4. Load BRef advanced stats and estimated metrics
  5. Populate players + stats + free_agents tables

Run once; subsequent runs use cache.
"""

import time
import json
import os

import requests
from bs4 import BeautifulSoup

from nba_api.stats.static import players as nba_players_static
from db.init_db import get_connection, init_db
from pipeline.cache import fetch_with_cache, save, load
from pipeline.bref_stats import load_bref_stats
from pipeline.estimated_metrics import fetch_estimated_metrics
from pipeline.utils import normalize_name

SPOTRAC_URL = 'https://www.spotrac.com/nba/free-agents/2027/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
STATS_SEASON = '2025-26'   # most recent complete season for scouting FAs
FA_SEASON = '2026-27'       # the season after which they become FAs


_normalize = normalize_name


def fetch_spotrac_fas() -> list[dict]:
    """
    Spotrac 2027 FA page has two tables:
      Table 1 (col layout): prior_team | _ | new_team | name | pos | yrs | total | AAV | status
                            → players who already re-signed; we capture as signed FAs
      Table 2 (col layout): name | pos | age | jersey | team | salary | fa_type
                            → full 2027 FA class with CBA type (UFA/RFA/Bird)
    We merge both, dedup by name, and use table 2's fa_type.
    """
    key = 'spotrac_fa_2027'
    cached = load(key)
    if cached:
        return cached

    time.sleep(2)
    r = requests.get(SPOTRAC_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')

    rows = []
    seen = set()

    # Table 2: full FA class (col0=name, col1=pos, col4=team, col5=salary, col6=type)
    if len(tables) >= 2:
        for row in tables[1].find_all('tr')[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cells) < 7:
                continue
            name = cells[0]
            if not name or name.isdigit():
                continue
            fa_type = cells[6].split('/')[0].strip()   # 'UFA' or 'RFA'
            rows.append({
                'name': name,
                'position': cells[1],
                'prior_team': cells[4],
                'prior_salary_str': cells[5],
                'fa_type': fa_type,
            })
            seen.add(name)

    # Table 1: already-signed (col3=name, col0=prior_team, col7=AAV)
    if tables:
        for row in tables[0].find_all('tr')[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cells) < 6:
                continue
            name = cells[3]
            if not name or name in seen:
                continue
            rows.append({
                'name': name,
                'position': cells[4],
                'prior_team': cells[0],
                'prior_salary_str': cells[7] if len(cells) > 7 else '',
                'fa_type': 'UFA',
            })
            seen.add(name)

    save(key, rows)
    return rows


_SPOTRAC_TO_NBA_NAME = {
    # Spotrac uses legal names; nba_api uses the names printed on jerseys.
    "nah'shon hyland": 'bones hyland',
    'trey jemison':    'trey jemison iii',
}


def build_nba_name_index() -> dict[str, int]:
    """Normalized name → NBA player ID from nba_api static list."""
    all_players = nba_players_static.get_players()
    idx = {}
    for p in all_players:
        key = _normalize(p['full_name'])
        idx[key] = p['id']
    # also add overrides
    for spotrac_key, nba_name in _SPOTRAC_TO_NBA_NAME.items():
        canonical = _normalize(nba_name)
        if canonical in idx:
            idx[spotrac_key] = idx[canonical]
    return idx


def parse_salary(s: str):
    digits = re.sub(r'[^\d]', '', s)
    return int(digits) if digits else None


def load_cached_leaguedash(season: str, measure: str) -> dict[int, dict]:
    path = os.path.join('data', 'cache', f'leaguedash_{measure}_{season}.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        rows = json.load(f)
    return {int(r['PLAYER_ID']): r for r in rows}


def run():
    init_db()

    print("Fetching 2027 free agent list from Spotrac...")
    fa_list = fetch_spotrac_fas()
    print(f"  {len(fa_list)} free agents found")

    name_idx = build_nba_name_index()

    base_idx = load_cached_leaguedash(STATS_SEASON, 'Base')
    adv_idx  = load_cached_leaguedash(STATS_SEASON, 'Advanced')
    est_idx  = fetch_estimated_metrics(STATS_SEASON)

    conn = get_connection()

    unmatched_id, no_stats = [], []
    loaded_count = 0

    for fa in fa_list:
        name = fa['name']
        key  = _normalize(name)
        nba_id = name_idx.get(key)

        if nba_id is None:
            unmatched_id.append(name)
            continue

        # Don't overwrite position if we already have one — Nets roster entries
        # from nets_stats.py are more reliable than Spotrac's position strings.
        conn.execute(
            """
            INSERT INTO players (id, name, position)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                position=COALESCE(excluded.position, players.position)
            """,
            (nba_id, name, fa.get('position')),
        )

        # load stats from cached 2025-26 data
        base = base_idx.get(nba_id)
        adv  = adv_idx.get(nba_id)
        est  = est_idx.get(nba_id)

        if base is None:
            no_stats.append(name)
        else:
            def f(d, k):
                try: return float(d[k])
                except: return None

            conn.execute(
                """
                INSERT INTO stats (
                    player_id, season, gp, mpg, pts, reb, ast, stl, blk, tov,
                    fg_pct, three_pct, three_pa, ft_pct,
                    ts_pct, efg_pct, usg_pct,
                    pts_per_75, per, bpm, vorp,
                    e_off_rating, e_def_rating, e_net_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_id, season) DO UPDATE SET
                    gp=excluded.gp, mpg=excluded.mpg,
                    pts=excluded.pts, reb=excluded.reb, ast=excluded.ast,
                    stl=excluded.stl, blk=excluded.blk, tov=excluded.tov,
                    fg_pct=excluded.fg_pct, three_pct=excluded.three_pct,
                    three_pa=excluded.three_pa, ft_pct=excluded.ft_pct,
                    ts_pct=excluded.ts_pct, efg_pct=excluded.efg_pct,
                    usg_pct=excluded.usg_pct,
                    e_off_rating=excluded.e_off_rating,
                    e_def_rating=excluded.e_def_rating,
                    e_net_rating=excluded.e_net_rating
                """,
                (
                    nba_id, STATS_SEASON,
                    base.get('GP'), f(base,'MIN'),
                    f(base,'PTS'), f(base,'REB'), f(base,'AST'),
                    f(base,'STL'), f(base,'BLK'), f(base,'TOV'),
                    f(base,'FG_PCT'), f(base,'FG3_PCT'), f(base,'FG3A'), f(base,'FT_PCT'),
                    f(adv,'TS_PCT') if adv else None,
                    f(adv,'EFG_PCT') if adv else None,
                    f(adv,'USG_PCT') if adv else None,
                    None, None, None, None,  # pts_per_75/per/bpm/vorp — filled by load_bref_stats() below
                    f(est,'E_OFF_RATING') if est else None,
                    f(est,'E_DEF_RATING') if est else None,
                    f(est,'E_NET_RATING') if est else None,
                ),
            )
            loaded_count += 1

        # populate free_agents table
        prior_salary = parse_salary(fa.get('prior_salary_str', ''))
        conn.execute(
            """
            INSERT INTO free_agents (player_id, season, type, prior_team, prior_salary)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(player_id, season) DO UPDATE SET
                type=excluded.type,
                prior_team=excluded.prior_team,
                prior_salary=excluded.prior_salary
            """,
            (nba_id, FA_SEASON, fa.get('fa_type', 'UFA'), fa['prior_team'], prior_salary),
        )

    conn.commit()
    conn.close()

    print(f"\nFA pool loaded: {loaded_count} with 2025-26 stats / {len(fa_list)} total FAs")
    if unmatched_id:
        print(f"  Could not find NBA ID for ({len(unmatched_id)}): {', '.join(unmatched_id[:10])}{'...' if len(unmatched_id)>10 else ''}")
    if no_stats:
        print(f"  No 2025-26 stats (likely rookie/overseas): {', '.join(no_stats[:10])}")

    # Now load BRef advanced stats for the FA pool (PER, BPM, VORP, pts/75)
    print("\nLoading BRef advanced stats for FA pool...")
    load_bref_stats(STATS_SEASON)


if __name__ == '__main__':
    run()
