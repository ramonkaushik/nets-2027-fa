"""
Load hardcoded contracts JSON into the contracts and cap_constants tables.
Matches players by normalized name against the players table (which must
already be populated by nets_stats.py).
"""

import json
import os
import re
import unicodedata

from db.init_db import get_connection

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _contracts_path(season: str) -> str:
    slug = season.replace('-', '_')
    return os.path.join(DATA_DIR, f'contracts_{slug}.json')


def normalize(name: str) -> str:
    nfkd = unicodedata.normalize('NFKD', str(name))
    ascii_ = nfkd.encode('ascii', 'ignore').decode()
    ascii_ = re.sub(r"\b(jr|sr|ii|iii|iv)\.?", '', ascii_, flags=re.IGNORECASE)
    return ' '.join(ascii_.lower().split())


def load_contracts(season: str = '2025-26'):
    with open(_contracts_path(season)) as f:
        data = json.load(f)

    season = data['season']
    conn = get_connection()

    # seed cap constants
    cc = data['cap_constants']
    conn.execute(
        """
        INSERT INTO cap_constants (season, salary_cap, tax_line, first_apron, second_apron)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(season) DO UPDATE SET
            salary_cap=excluded.salary_cap,
            tax_line=excluded.tax_line,
            first_apron=excluded.first_apron,
            second_apron=excluded.second_apron
        """,
        (season, cc['salary_cap'], cc['tax_line'], cc['first_apron'], cc['second_apron']),
    )

    # build name → player_id map from DB
    db_players = conn.execute("SELECT id, name FROM players").fetchall()
    name_to_id = {normalize(p['name']): p['id'] for p in db_players}

    unmatched = []

    for c in data['contracts']:
        key = normalize(c['name'])
        player_id = name_to_id.get(key)
        if player_id is None:
            unmatched.append(c['name'])
            continue

        conn.execute(
            """
            INSERT INTO contracts (player_id, season, salary, years_left, option_type, guaranteed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id, season) DO UPDATE SET
                salary=excluded.salary,
                years_left=excluded.years_left,
                option_type=excluded.option_type,
                guaranteed=excluded.guaranteed
            """,
            (
                player_id, season,
                c['salary'], c['years_left'],
                c['option_type'], c['guaranteed'],
            ),
        )

    conn.commit()
    conn.close()

    loaded = len(data['contracts']) - len(unmatched)
    print(f"Contracts loaded: {loaded}/{len(data['contracts'])} for {season}.")
    if unmatched:
        print(f"UNMATCHED contracts — no player row found for: {', '.join(unmatched)}")
    else:
        print("All contracts matched cleanly.")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--season', default='2025-26')
    args = p.parse_args()
    load_contracts(args.season)
