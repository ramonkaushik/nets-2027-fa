"""
Brooklyn Nets front-office evaluation tool.

Usage:
  python main.py           # show current 2026-27 roster, cap, and 2027 FA pool
  python main.py --rebuild # re-run data pipeline before displaying
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db.init_db import get_connection


# ── helpers ──────────────────────────────────────────────────────────────────

def _m(n):
    """Format dollars as $XM."""
    return f"${n/1e6:.1f}M" if n else "—"

def _pct(v):
    return f"{v*100:.1f}%" if v is not None else "—"

def _f(v, fmt=".1f"):
    return format(v, fmt) if v is not None else "—"

def _sgn(v, fmt=".1f"):
    return f"{v:+{fmt}}" if v is not None else "—"


# ── section 1: nets roster ────────────────────────────────────────────────────

def print_nets_roster(roster_season: str, stats_season: str):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT p.name, p.position,
               c.salary, c.years_left, c.option_type,
               s.gp, s.mpg, s.pts, s.reb, s.ast,
               s.ts_pct, s.usg_pct,
               s.bpm, s.vorp, s.e_net_rating, s.pts_per_75
        FROM players p
        JOIN contracts c ON p.id = c.player_id AND c.season = ?
        LEFT JOIN stats s ON p.id = s.player_id AND s.season = ?
        ORDER BY c.salary DESC
        """,
        (roster_season, stats_season),
    ).fetchall()
    conn.close()

    W = 108
    print()
    print("=" * W)
    print(f"  BROOKLYN NETS — {roster_season} ROSTER  (stats from {stats_season} season)")
    print("=" * W)
    print(
        f"  {'PLAYER':<24} {'POS':<5} {'SALARY':>8}  {'OPT':<6}  "
        f"{'GP':>3} {'MPG':>4} {'PTS':>4} {'REB':>4} {'AST':>4}  "
        f"{'TS%':>5} {'USG%':>5}  "
        f"{'BPM':>5} {'VORP':>5} {'E_NET':>6} {'P/75':>5}"
    )
    print("  " + "-" * (W - 2))
    for r in rows:
        opt = {"none": "—", "player": "PLR", "team": "TM"}.get(r["option_type"] or "none", "—")
        print(
            f"  {r['name']:<24} {(r['position'] or '?'):<5} "
            f"{_m(r['salary']):>8}  {opt:<6}  "
            f"{(r['gp'] or 0):>3} {(r['mpg'] or 0):>4.1f} "
            f"{(r['pts'] or 0):>4.1f} {(r['reb'] or 0):>4.1f} {(r['ast'] or 0):>4.1f}  "
            f"{_pct(r['ts_pct']):>5} {_pct(r['usg_pct']):>5}  "
            f"{_sgn(r['bpm']):>5} {_sgn(r['vorp']):>5} "
            f"{_sgn(r['e_net_rating']):>6} {_f(r['pts_per_75']):>5}"
        )
    print()


# ── section 2: cap summary ───────────────────────────────────────────────────

def print_cap_summary(season: str):
    conn = get_connection()
    cap = conn.execute(
        "SELECT * FROM cap_constants WHERE season=?", (season,)
    ).fetchone()
    if not cap:
        conn.close()
        print(f"  No cap constants for {season}.")
        return

    contracts = conn.execute(
        """
        SELECT c.salary, c.years_left, c.option_type
        FROM contracts c WHERE c.season=?
        """,
        (season,),
    ).fetchall()
    conn.close()

    committed = sum(r["salary"] for r in contracts if r["salary"])
    expiring  = sum(r["salary"] for r in contracts if r["salary"] and r["years_left"] == 0)
    tax_delta = cap["tax_line"] - committed

    W = 108
    print("=" * W)
    print(f"  CAP SUMMARY — {season}")
    print("=" * W)
    print(f"  {'Salary cap':.<35} {_m(cap['salary_cap'])}")
    print(f"  {'Committed salary':.<35} {_m(committed)}")
    print(f"  {'Expiring after this season':.<35} {_m(expiring)}  ({len([r for r in contracts if r['years_left']==0])} players)")
    print(f"  {'Projected 2027 committed':.<35} {_m(committed - expiring)}")
    print()
    sign = "OVER" if tax_delta < 0 else "under"
    print(f"  {'Luxury tax line':.<35} {_m(cap['tax_line'])}  [{_m(abs(tax_delta))} {sign}]")
    print(f"  {'1st apron':.<35} {_m(cap['first_apron'])}  [{_m(abs(cap['first_apron']-committed))} {'over' if committed > cap['first_apron'] else 'under'}]")
    print(f"  {'2nd apron':.<35} {_m(cap['second_apron'])}  [{_m(abs(cap['second_apron']-committed))} {'over' if committed > cap['second_apron'] else 'under'}]")
    print()


# ── section 3: 2027 FA pool ──────────────────────────────────────────────────

def print_fa_pool(fa_season: str, stats_season: str, min_gp: int = 20, limit: int = 40):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT p.name, p.position, fa.prior_team, fa.type,
               s.gp, s.mpg, s.pts, s.reb, s.ast,
               s.ts_pct, s.usg_pct,
               s.bpm, s.vorp, s.e_net_rating, s.pts_per_75
        FROM free_agents fa
        JOIN players p ON p.id = fa.player_id
        JOIN stats s ON s.player_id = fa.player_id AND s.season = ?
        WHERE fa.season = ?
          AND (s.gp IS NULL OR s.gp >= ?)
        ORDER BY s.bpm DESC
        LIMIT ?
        """,
        (stats_season, fa_season, min_gp, limit),
    ).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) FROM free_agents WHERE season=?", (fa_season,)
    ).fetchone()[0]
    conn.close()

    W = 108
    print("=" * W)
    print(f"  2027 FREE AGENT POOL  (top {limit} of {total} by BPM, min {min_gp} GP)")
    print(f"  Stats from {stats_season} season  |  These are LEAGUE-WIDE free agents, NOT Nets players")
    print("=" * W)
    print(
        f"  {'PLAYER':<24} {'POS':<5} {'TM':<5} {'TYPE':<5}  "
        f"{'GP':>3} {'MPG':>4} {'PTS':>4} {'REB':>4} {'AST':>4}  "
        f"{'TS%':>5} {'USG%':>5}  "
        f"{'BPM':>5} {'VORP':>5} {'E_NET':>6} {'P/75':>5}"
    )
    print("  " + "-" * (W - 2))
    for r in rows:
        print(
            f"  {r['name']:<24} {(r['position'] or '?'):<5} "
            f"{(r['prior_team'] or '?'):<5} {(r['type'] or 'UFA'):<5}  "
            f"{(r['gp'] or 0):>3} {(r['mpg'] or 0):>4.1f} "
            f"{(r['pts'] or 0):>4.1f} {(r['reb'] or 0):>4.1f} {(r['ast'] or 0):>4.1f}  "
            f"{_pct(r['ts_pct']):>5} {_pct(r['usg_pct']):>5}  "
            f"{_sgn(r['bpm']):>5} {_sgn(r['vorp']):>5} "
            f"{_sgn(r['e_net_rating']):>6} {_f(r['pts_per_75']):>5}"
        )
    print()


# ── pipeline ──────────────────────────────────────────────────────────────────

def rebuild():
    from pipeline.nets_stats import load_season
    from pipeline.bref_stats import load_bref_stats
    from pipeline.load_contracts import load_contracts
    from pipeline.estimated_metrics import load_estimated_metrics
    from pipeline.update_to_2026_27 import run as update_2026_27
    from pipeline.fa_pool_2027 import run as build_fa_pool

    print("── nba_api: 2025-26 Nets stats ──")
    load_season('2025-26')
    print("\n── BRef: advanced stats 2025-26 ──")
    load_bref_stats('2025-26')
    print("\n── Contracts + cap constants ──")
    load_contracts('2025-26')
    load_contracts('2026-27')
    print("\n── Estimated metrics (E_NET_RATING) ──")
    load_estimated_metrics('2025-26')
    print("\n── 2026-27 roster migration ──")
    update_2026_27()
    print("\n── 2027 FA pool ──")
    build_fa_pool()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild', action='store_true',
                        help='Re-run data pipeline before displaying')
    parser.add_argument('--min-gp', type=int, default=20,
                        help='Minimum GP filter for FA pool (default 20)')
    parser.add_argument('--fa-limit', type=int, default=40,
                        help='Number of FAs to show (default 40)')
    args = parser.parse_args()

    if args.rebuild:
        rebuild()

    print_nets_roster(roster_season='2026-27', stats_season='2025-26')
    print_cap_summary(season='2026-27')
    print_fa_pool(fa_season='2026-27', stats_season='2025-26',
                  min_gp=args.min_gp, limit=args.fa_limit)
