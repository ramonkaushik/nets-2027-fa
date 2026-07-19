"""
Declares Schema and connects to SQLite DB
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'nets.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    position          TEXT,
    age               INTEGER,
    years_of_service  INTEGER
);

CREATE TABLE IF NOT EXISTS contracts (
    player_id    INTEGER NOT NULL,
    season       TEXT NOT NULL,
    salary       INTEGER,
    years_left   INTEGER,
    option_type  TEXT,
    guaranteed   INTEGER,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS stats (
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
    e_off_rating  REAL,
    e_def_rating  REAL,
    e_net_rating  REAL,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS free_agents (
    player_id     INTEGER NOT NULL,
    season        TEXT NOT NULL,
    type          TEXT,
    prior_team    TEXT,
    prior_salary  INTEGER,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(id)
);
"""


def get_db_path():
    return os.path.abspath(DB_PATH)


def get_connection():
    path = get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # lets callers do row['salary'] instead of row[2]
    return conn


def init_db():
    path = get_db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"DB initialized at {path}")


if __name__ == '__main__':
    init_db()
