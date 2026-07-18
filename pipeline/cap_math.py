"""
Cap math: committed salary, cap space, and distance to tax/apron lines.
All values in whole dollars.
"""

from db.init_db import get_connection


def get_cap_summary(season: str) -> dict:
    conn = get_connection()

    cap = conn.execute(
        "SELECT * FROM cap_constants WHERE season=?", (season,)
    ).fetchone()

    if cap is None:
        conn.close()
        raise ValueError(f"No cap constants for season {season!r} — run load_contracts first.")

    contracts = conn.execute(
        """
        SELECT p.name, p.position, c.salary, c.years_left, c.option_type, c.guaranteed
        FROM contracts c
        JOIN players p ON p.id = c.player_id
        WHERE c.season=?
        ORDER BY c.salary DESC
        """,
        (season,),
    ).fetchall()

    conn.close()

    committed = sum(r['salary'] for r in contracts)

    return {
        'season': season,
        'salary_cap': cap['salary_cap'],
        'tax_line': cap['tax_line'],
        'first_apron': cap['first_apron'],
        'second_apron': cap['second_apron'],
        'committed_salary': committed,
        'cap_space': max(0, cap['salary_cap'] - committed),
        'distance_to_tax': cap['tax_line'] - committed,
        'distance_to_first_apron': cap['first_apron'] - committed,
        'distance_to_second_apron': cap['second_apron'] - committed,
        'contracts': [dict(r) for r in contracts],
    }


def print_cap_summary(season: str):
    s = get_cap_summary(season)
    cap = s['salary_cap']
    committed = s['committed_salary']

    def fmt(n):
        return f"${n/1e6:.1f}M"

    print(f"\n{'='*55}")
    print(f"Brooklyn Nets — {season} Cap Summary")
    print(f"{'='*55}")
    print(f"  Salary cap:         {fmt(cap)}")
    print(f"  Committed salary:   {fmt(committed)}")
    print(f"  Cap space:          {fmt(s['cap_space'])}")
    print(f"  {'Over' if s['distance_to_tax'] < 0 else 'Under'} tax line:      "
          f"{fmt(abs(s['distance_to_tax']))} {'over' if s['distance_to_tax'] < 0 else 'under'} ({fmt(s['tax_line'])})")
    print(f"  Distance to 1st apron: {fmt(abs(s['distance_to_first_apron']))} "
          f"({'over' if s['distance_to_first_apron'] < 0 else 'under'})")
    print(f"  Distance to 2nd apron: {fmt(abs(s['distance_to_second_apron']))} "
          f"({'over' if s['distance_to_second_apron'] < 0 else 'under'})")
    print(f"\n{'Player':<25} {'Pos':<5} {'Salary':>10}  {'Yrs':>3}  Option")
    print('-' * 55)
    for c in s['contracts']:
        print(f"  {c['name']:<23} {(c['position'] or '?'):<5} "
              f"{fmt(c['salary']):>9}  {c['years_left']:>3}  {c['option_type']}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--season', default='2025-26')
    args = p.parse_args()
    print_cap_summary(args.season)
