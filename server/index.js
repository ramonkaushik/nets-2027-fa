const express = require('express')
const cors    = require('cors')
const path    = require('path')
const Database = require('better-sqlite3')

const app = express()
const PORT     = process.env.PORT ?? 8000
const DB_PATH  = process.env.DB_PATH ?? path.join(__dirname, '..', 'data', 'nets.db')
const ORIGINS  = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(',')
  : ['http://localhost:5173']

// ── season config ────────────────────────────────────────────────────────────
// Update these each offseason: bump ROSTER_SEASON to the new year,
// set STATS_SEASON to the last completed season, update the cap numbers.
const ROSTER_SEASON = '2026-27'
const STATS_SEASON  = '2025-26'

const CAP_2026_27 = {
  salary_cap:   148_000_000,
  tax_line:     180_500_000,
  first_apron:  187_600_000,
  second_apron: 198_400_000,
}

app.use(cors({ origin: ORIGINS }))

// Open a fresh readonly connection per request — better-sqlite3 is synchronous
// so there's no connection pool; the overhead is negligible for a local tool.
function db() {
  return new Database(DB_PATH, { readonly: true })
}

// ── GET /api/roster ──────────────────────────────────────────────────────────
app.get('/api/roster', (req, res) => {
  const rows = db().prepare(`
    SELECT
      p.id, p.name, p.position,
      c.salary, c.years_left, c.option_type,
      s.gp, s.mpg, s.pts, s.reb, s.ast, s.stl, s.blk, s.tov,
      s.ts_pct, s.efg_pct, s.usg_pct,
      s.bpm, s.vorp, s.per, s.pts_per_75,
      s.e_off_rating, s.e_def_rating, s.e_net_rating
    FROM players p
    JOIN contracts c ON p.id = c.player_id AND c.season = ?
    LEFT JOIN stats s ON p.id = s.player_id AND s.season = ?
    ORDER BY c.salary DESC
  `).all(ROSTER_SEASON, STATS_SEASON)

  res.json(rows)
})

// ── GET /api/cap ─────────────────────────────────────────────────────────────
app.get('/api/cap', (req, res) => {
  const contracts = db().prepare(
    'SELECT salary, years_left FROM contracts WHERE season = ?'
  ).all(ROSTER_SEASON)

  const cap = CAP_2026_27
  const committed = contracts.reduce((s, r) => s + (r.salary ?? 0), 0)
  const expiring  = contracts.reduce((s, r) => s + (r.years_left === 0 ? (r.salary ?? 0) : 0), 0)

  res.json({
    season: ROSTER_SEASON,
    salary_cap:     cap.salary_cap,
    tax_line:       cap.tax_line,
    first_apron:    cap.first_apron,
    second_apron:   cap.second_apron,
    committed,
    expiring,
    projected_next:  committed - expiring,
    space_vs_cap:    Math.max(0, cap.salary_cap - committed),
    room_to_tax:     cap.tax_line - committed,
    room_to_apron1:  cap.first_apron - committed,
    room_to_apron2:  cap.second_apron - committed,
  })
})

// ── GET /api/free-agents ─────────────────────────────────────────────────────

// sort_by is injected directly into the SQL string (SQLite can't parameterize
// column names), so we whitelist it to prevent SQL injection.
const VALID_SORTS = new Set([
  'bpm', 'vorp', 'pts', 'reb', 'ast', 'ts_pct',
  'e_net_rating', 'pts_per_75', 'per', 'mpg', 'gp',
])

app.get('/api/free-agents', (req, res) => {
  const minGP    = parseInt(req.query.min_gp ?? '20', 10)
  const position = req.query.position ?? ''
  const sortBy   = VALID_SORTS.has(req.query.sort_by) ? req.query.sort_by : 'bpm'
  const limit    = Math.min(parseInt(req.query.limit ?? '60', 10), 200)

  const posClause = position ? `AND (p.position LIKE '%' || ? || '%')` : ''
  const params = position
    ? [STATS_SEASON, ROSTER_SEASON, minGP, position, limit]
    : [STATS_SEASON, ROSTER_SEASON, minGP, limit]

  const rows = db().prepare(`
    SELECT
      p.id, p.name, p.position, fa.prior_team, fa.type AS fa_type,
      s.gp, s.mpg, s.pts, s.reb, s.ast, s.stl, s.blk, s.tov,
      s.ts_pct, s.efg_pct, s.usg_pct,
      s.bpm, s.vorp, s.per, s.pts_per_75,
      s.e_off_rating, s.e_def_rating, s.e_net_rating
    FROM free_agents fa
    JOIN players p ON p.id = fa.player_id
    JOIN stats s   ON s.player_id = fa.player_id AND s.season = ?
    WHERE fa.season = ?
      AND (s.gp IS NULL OR s.gp >= ?)
      ${posClause}
    ORDER BY s.${sortBy} DESC NULLS LAST
    LIMIT ?
  `).all(...params)

  res.json(rows)
})

app.listen(PORT, () => {
  console.log(`Nets API running on http://localhost:${PORT}`)
})
