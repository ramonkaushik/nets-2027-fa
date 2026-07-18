# NBA Free Agent Evaluation Tool — Project Context Handoff

Paste this into Claude Code to carry over the full context.

---

## WHAT THIS IS

A personal project to strengthen a job application for a **Senior Full Stack Engineer** role at a company building software for the **Brooklyn Nets** front office (player evaluation, scouting, roster management). Building it demonstrates real NBA knowledge + engineering ability, which the job explicitly wants.

**Positioning (important):** This is a front-office *tool* that surfaces options and exposes tradeoffs — NOT a "here's who the Nets should sign" hot take. It helps someone explore the decision space. Frame everything that way. The goal is to present free agents that would be good for the team to sign given the 2025-2026 roster after the season ended. Consider resigning RFAs if the stats think it is a good idea. 

**Stack (matches the JD):** Python for data pipeline, React + TypeScript (React) for UI, SQLite for storage.

**Approach:** Start small, expand scope. Ship each step working before the next.

---

## STAGE 1 SCOPE (build this first)

Data foundation only. No recommendations yet.

1. Nets roster + contracts for a given season → committed salary, cap space
2. Free agent pool with UFA/RFA classification
3. Per-player stats — Nets players AND free agents
4. Cap constants for the season (cap, tax line, apron)

Contracts and cap data are **hardcoded (JSON)** for Stage 1 — acceptable and unblocks development. Stats come from `nba_api`.

---

## THE HARD PARTS (design deliberately)

1. **Player ID mapping** — stats source (`nba_api`) and hardcoded contract JSON won't share a key. Pick a canonical ID (use NBA's player ID) and build a mapping layer. Name matching is error-prone (suffixes, accents, nicknames). This is the #1 time sink.

2. **Data integrity** — every roster player and FA must resolve to a stats record OR be explicitly flagged as unmatched. NO silent drops. An unmatched player is a visible error, not a missing row. (Same instinct as a golden-file test harness — prove completeness.)

3. **`nba_api` reliability** — unofficial wrapper around NBA.com endpoints. Rate limits, occasional breakage. Cache responses aggressively so demos don't depend on live network.

---

## STATS TO CAPTURE (this reflects real front-office thinking)

The thesis: raw counting stats reward volume and role, not quality. Rank by **efficiency-adjusted production per dollar, filtered by positional need** — not by PPG.

Tiered:
- **Availability:** gp, mpg
- **Volume (box score):** pts, reb, ast, stl, blk, tov
- **Shooting:** fg_pct, three_pct, three_pa (volume matters!), ft_pct
- **Efficiency (where quality shows):** ts_pct (True Shooting — best single scoring metric), efg_pct, usg_pct (usage rate — context for everything), pts_per_75 (ties usage to output, normalizes for pace)
- **Impact (all-in-one):** per (dated, include for familiarity), bpm (Box Plus/Minus), vorp (Value Over Replacement)

Progression = volume → efficiency → impact = how a front office reads a player.

**Data sources:**
- Volume, shooting, gp/mpg → `nba_api` directly
- ts_pct, efg_pct, usg_pct → `nba_api` advanced endpoint (or compute)
- per, bpm, vorp → Basketball Reference (nba_api lacks these; hardcode or scrape)

---

## SQLITE SCHEMA

```sql
CREATE TABLE players (
    id                INTEGER PRIMARY KEY,   -- canonical NBA player ID
    name              TEXT NOT NULL,
    position          TEXT,
    age               INTEGER,
    years_of_service  INTEGER
);

CREATE TABLE contracts (
    player_id    INTEGER NOT NULL,
    season       TEXT NOT NULL,
    salary       INTEGER,
    years_left   INTEGER,
    option_type  TEXT,                        -- 'none' | 'player' | 'team'
    guaranteed   INTEGER,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE stats (
    player_id     INTEGER NOT NULL,
    season        TEXT NOT NULL,
    gp            INTEGER,
    mpg           REAL,
    pts           REAL,
    reb           REAL,
    ast           REAL,
    stl           REAL,
    blk           REAL,
    tov           REAL,
    fg_pct        REAL,
    three_pct     REAL,
    three_pa      REAL,
    ft_pct        REAL,
    ts_pct        REAL,
    efg_pct       REAL,
    usg_pct       REAL,
    pts_per_75    REAL,
    per           REAL,
    bpm           REAL,
    vorp          REAL,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE free_agents (
    player_id     INTEGER NOT NULL,
    season        TEXT NOT NULL,
    type          TEXT,                        -- 'UFA' | 'RFA'
    prior_team    TEXT,
    prior_salary  INTEGER,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE cap_constants (
    season        TEXT PRIMARY KEY,
    salary_cap    INTEGER,
    tax_line      INTEGER,
    first_apron   INTEGER,
    second_apron  INTEGER
);
```

Notes:
- SQLite uses REAL for decimals, INTEGER for whole numbers (no DECIMAL type).
- Composite PK (player_id, season) = one row per player per season, supports multiple seasons without redesign.
- Data is relational (player → contract → stats → FA status). SQL is the right call, NOT NoSQL. SQLite = zero setup, SQL is on the JD, trivial to swap to Postgres later.

---

## DESIGN PRINCIPLES TO FOLLOW

- **Season-agnostic:** season is an input parameter everywhere, cap constants keyed by season. Enables retrospective or forward-looking use.
- **Testability:** data loading behind interfaces so the stats source can be faked in tests. Cap math unit-testable without network calls.
- **Reproducibility:** cache API responses. Same season input → same output.
- **Layered:** keep data-fetch, storage, and business logic in separate modules with clear boundaries.

---

## BUILD ORDER

1. SQLite schema + DB init
2. Stats pipeline for ONE team via nba_api — prove the API works end to end
3. Player ID mapping layer (canonical ID, handle name mismatches)
4. Hardcoded contracts + roster JSON, joined to stats via ID mapping
5. Cap math — committed salary, cap space, distance to tax/apron
6. Free agent pool JSON + their stats
7. Single joined output view (player → contract → stats), plus cap summary

Ship each working before moving on.

---

## STAGE 2 PREVIEW (not now — keep scope tight)

- Positional/statistical needs analysis for the roster
- Candidate ranking with EXPOSED reasoning (not a black box) — rank by value-per-dollar filtered by need
- Cap exceptions (MLE, bi-annual, Bird rights) — the real CBA complexity
- React/TS UI: user sets cap room + positional needs + priorities, tool surfaces and ranks options with tradeoffs visible

---

## FIRST ASK FOR CLAUDE CODE

Set up the project structure, create the SQLite schema, and build step 2: a Python script using `nba_api` that pulls current-season per-player stats for the Brooklyn Nets roster and loads them into the stats table. Cache the API responses. Flag any player that doesn't resolve cleanly rather than dropping them. Don't overcomplicate it.
