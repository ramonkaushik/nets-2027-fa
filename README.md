# Brooklyn Nets Front Office Tool

A full-stack analytics tool for evaluating the 2026-27 Nets roster, modeling cap scenarios, and scouting the 2027 free agent class.

---

## What's in here

```
pipeline/       Python scripts that pull data from NBA.com, Basketball Reference, and Spotrac
db/             SQLite schema definition
data/nets.db    The pre-populated database (~100KB, committed to the repo)
server/         Node.js/Express API that serves the database
ui/             React + TypeScript frontend
main.py         CLI view of the roster, cap, and FA pool (useful for quick checks)
```

---

## Running it

The database is already populated. You don't need to run the pipeline to use the app.

### API server
```bash
cd server
npm install
npm start          # runs on http://localhost:8000
# or
npm run dev        # same but auto-restarts on file changes
```

### Frontend
```bash
cd ui
npm install
npm run dev        # opens on http://localhost:5173
```

### CLI (optional, no server needed)
```bash
pip install -r requirements.txt
python main.py              # roster + cap + top 40 FAs by BPM
python main.py --min-gp 30  # stricter GP filter on FA pool
python main.py --rebuild    # re-run the full data pipeline first
```

---

## Updating for next season

Three places to change, in order:

**1. Bump the season constants** (both files)

`server/index.js` and `main.py` each have a season config block at the top:
```js
// server/index.js
const ROSTER_SEASON = '2027-28'   // was 2026-27
const STATS_SEASON  = '2026-27'   // was 2025-26
```
```python
# main.py
ROSTER_SEASON = '2027-28'
STATS_SEASON  = '2026-27'
```


## Data sources and their quirks

| Source | What it provides | Notes |
|--------|-----------------|-------|
| `nba_api` | Roster, per-game stats, estimated metrics | Unofficial wrapper around NBA.com endpoints. Can break if NBA changes their API. Add `time.sleep(1)` between calls if you get rate-limited. |
| Basketball Reference | BPM, VORP, PER, Pts/75 | No public API — scraped via `requests` + `pandas`. BRef asks for a 3-second delay between requests (already built in). Scraper will break if they restructure the page HTML. |
| Spotrac | Free agent class, contract values | No public API — scraped. Page structure has changed before; if the FA pool comes back empty, inspect the table columns in `pipeline/fa_pool_2027.py`. |

---

## Limitations

**Cap numbers are estimates until official.** The salary cap, tax line, and aprons are set each July. The numbers in this tool are projections based on the current CBA formula — verify against the official NBPA memo before using for real decisions.

**The database is a snapshot, not live.** Stats reflect the 2025-26 regular season. The pipeline runs once; it doesn't update automatically. Run `python main.py --rebuild` after any pipeline script changes to refresh the data.