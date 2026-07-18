import { useMemo, useState } from 'react'
import { useApi } from './hooks/useApi'
import { StatTable, type ColDef } from './components/StatTable'
import { CapBar } from './components/CapBar'
import { SignModal } from './components/SignModal'
import { ShimmerButton } from './components/magicui/ShimmerButton'
import { cn } from './lib/utils'
import type { Player, FreeAgent, CapSummary } from './types'

// ── types ─────────────────────────────────────────────────────────────────────

interface Signing { player: FreeAgent; salary: number; years: number }

// ── formatters ────────────────────────────────────────────────────────────────

const M   = (v: unknown) => v == null ? '—' : `$${((v as number) / 1e6).toFixed(1)}M`
const pct = (v: unknown) => v == null ? '—' : `${((v as number) * 100).toFixed(1)}%`
const sgn = (v: unknown) => v == null ? '—' : `${(v as number) > 0 ? '+' : ''}${(v as number).toFixed(1)}`
const f1  = (v: unknown) => v == null ? '—' : (v as number).toFixed(1)

const OPT_LABEL: Record<string, string> = { player: 'PO', team: 'TO', none: '' }

// ── column defs ───────────────────────────────────────────────────────────────

const ROSTER_COLS: ColDef<Player>[] = [
  { key: 'name',         label: 'Player',  align: 'left', sticky: true, fmt: v => String(v ?? '') },
  { key: 'position',     label: 'Pos',     align: 'left', fmt: v => String(v ?? '?') },
  { key: 'salary',       label: 'Salary',  fmt: M,        title: '2026-27 salary' },
  { key: 'years_left',   label: 'Yrs',     title: 'Years remaining after 2026-27', fmt: v => v == null ? '—' : String(v) },
  { key: 'option_type',  label: 'Opt',     align: 'left', fmt: v => OPT_LABEL[String(v ?? 'none')] ?? '' },
  { key: 'gp',           label: 'GP',      title: 'Games played (2025-26)' },
  { key: 'mpg',          label: 'MPG',     fmt: f1 },
  { key: 'pts',          label: 'PTS',     fmt: f1 },
  { key: 'reb',          label: 'REB',     fmt: f1 },
  { key: 'ast',          label: 'AST',     fmt: f1 },
  { key: 'ts_pct',       label: 'TS%',     fmt: pct, title: 'True Shooting %' },
  { key: 'usg_pct',      label: 'USG%',    fmt: pct, title: 'Usage rate' },
  { key: 'bpm',          label: 'BPM',     fmt: sgn, title: 'Box Plus/Minus (BRef)' },
  { key: 'vorp',         label: 'VORP',    fmt: sgn, title: 'Value Over Replacement Player' },
  { key: 'e_net_rating', label: 'E_NET',   fmt: sgn, title: 'Estimated Net Rating (NBA.com)' },
  { key: 'pts_per_75',   label: 'P/75',    fmt: f1,  title: 'Points per 75 possessions' },
]

const FA_COLS: ColDef<FreeAgent>[] = [
  { key: 'name',         label: 'Player',  align: 'left', sticky: true, fmt: v => String(v ?? '') },
  { key: 'position',     label: 'Pos',     align: 'left', fmt: v => String(v ?? '?') },
  { key: 'prior_team',   label: 'Team',    align: 'left', fmt: v => String(v ?? '?') },
  { key: 'fa_type',      label: 'Type',    align: 'left', fmt: v => String(v ?? 'UFA') },
  { key: 'gp',           label: 'GP' },
  { key: 'mpg',          label: 'MPG',     fmt: f1 },
  { key: 'pts',          label: 'PTS',     fmt: f1 },
  { key: 'reb',          label: 'REB',     fmt: f1 },
  { key: 'ast',          label: 'AST',     fmt: f1 },
  { key: 'ts_pct',       label: 'TS%',     fmt: pct, title: 'True Shooting %' },
  { key: 'usg_pct',      label: 'USG%',    fmt: pct, title: 'Usage rate' },
  { key: 'bpm',          label: 'BPM',     fmt: sgn, title: 'Box Plus/Minus (BRef)' },
  { key: 'vorp',         label: 'VORP',    fmt: sgn, title: 'Value Over Replacement Player' },
  { key: 'e_net_rating', label: 'E_NET',   fmt: sgn, title: 'Estimated Net Rating (NBA.com)' },
  { key: 'pts_per_75',   label: 'P/75',    fmt: f1,  title: 'Points per 75 possessions' },
]

// ── section ───────────────────────────────────────────────────────────────────

function Section({ title, sub, badge, children, actions }: {
  title: string
  sub?: string
  badge?: string
  children: React.ReactNode
  actions?: React.ReactNode
}) {
  return (
    <section className="mb-14">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <h2 className="text-base font-semibold text-white tracking-tight">{title}</h2>
            {badge && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/20">
                {badge}
              </span>
            )}
          </div>
          {sub && <p className="text-[11px] text-zinc-600">{sub}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  )
}

// ── pill select ────────────────────────────────────────────────────────────────

function FilterSelect({ label, value, onChange, children }: {
  label: string
  value: string | number
  onChange: (v: string) => void
  children: React.ReactNode
}) {
  return (
    <label className="flex items-center gap-1.5">
      <span className="text-[10px] uppercase tracking-widest text-zinc-600 font-medium">{label}</span>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="text-xs bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5
          text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500/50
          focus:border-indigo-500/50 transition-colors hover:border-zinc-700 cursor-pointer"
      >
        {children}
      </select>
    </label>
  )
}

// ── app ───────────────────────────────────────────────────────────────────────

export default function App() {
  const { data: roster, loading: rLoad } = useApi<Player[]>('/api/roster')
  const { data: cap,    loading: cLoad } = useApi<CapSummary>('/api/cap')

  const [minGP,  setMinGP]  = useState(20)
  const [pos,    setPos]    = useState('')
  const [sortBy, setSortBy] = useState('bpm')

  const faUrl = `/api/free-agents?min_gp=${minGP}&position=${encodeURIComponent(pos)}&sort_by=${sortBy}&limit=60`
  const { data: fas, loading: fLoad } = useApi<FreeAgent[]>(faUrl)

  // ── builder state ──────────────────────────────────────────────────────────
  const [removedIds, setRemovedIds] = useState<Set<number>>(new Set())
  const [signings,   setSignings]   = useState<Signing[]>([])
  const [signTarget, setSignTarget] = useState<FreeAgent | null>(null)

  const signingIds = useMemo(() => new Set(signings.map(s => s.player.id)), [signings])

  const workingRoster = useMemo((): Player[] => {
    const base  = (roster ?? []).filter(p => !removedIds.has(p.id))
    const added = signings.map(s => ({
      ...s.player,
      salary:      s.salary,
      years_left:  s.years - 1,
      option_type: null as string | null,
    }))
    return [...base, ...added]
  }, [roster, removedIds, signings])

  const computedCap = useMemo((): CapSummary | null => {
    if (!cap) return null
    const committed = workingRoster.reduce((s, p) => s + (p.salary ?? 0), 0)
    const expiring  = workingRoster
      .filter(p => (p.years_left ?? 1) <= 0)
      .reduce((s, p) => s + (p.salary ?? 0), 0)
    return {
      ...cap,
      committed,
      expiring,
      projected_next: committed - expiring,
      space_vs_cap:   Math.max(0, cap.salary_cap - committed),
      room_to_tax:    cap.tax_line - committed,
      room_to_apron1: cap.first_apron - committed,
      room_to_apron2: cap.second_apron - committed,
    }
  }, [cap, workingRoster])

  const capDelta   = computedCap && cap ? computedCap.committed - cap.committed : 0
  const hasChanges = removedIds.size > 0 || signings.length > 0

  // ── handlers ───────────────────────────────────────────────────────────────
  function removePlayer(id: number) { setRemovedIds(prev => new Set([...prev, id])) }
  function unsignPlayer(id: number) { setSignings(prev => prev.filter(s => s.player.id !== id)) }
  function handleSign(salary: number, years: number) {
    if (!signTarget) return
    setSignings(prev => [...prev, { player: signTarget, salary, years }])
    setSignTarget(null)
  }
  function resetRoster() { setRemovedIds(new Set()); setSignings([]) }

  // ── render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen text-zinc-200" style={{ background: '#080808' }}>
      {signTarget && (
        <SignModal player={signTarget} onConfirm={handleSign} onCancel={() => setSignTarget(null)} />
      )}

      {/* ── header ────────────────────────────────────────────────────────── */}
      <header className="border-b border-white/[0.06] bg-zinc-950">
        <div className="px-6 md:px-10 py-5 max-w-screen-2xl mx-auto">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <img src="/netslogo.png" alt="Brooklyn Nets" className="w-11 h-11 select-none" draggable={false} />
              {hasChanges && (
                <div className="flex items-center gap-2 pl-4 border-l border-white/[0.08]">
                  {removedIds.size > 0 && (
                    <span className="text-xs text-amber-400 tabular-nums">−{removedIds.size} out</span>
                  )}
                  {signings.length > 0 && (
                    <span className="text-xs text-emerald-400 tabular-nums">+{signings.length} signed</span>
                  )}
                  <span className={cn(
                    'text-xs font-semibold tabular-nums',
                    capDelta >= 0 ? 'text-red-400' : 'text-emerald-400',
                  )}>
                    {capDelta >= 0 ? '+' : '−'}${Math.abs(capDelta / 1e6).toFixed(1)}M cap
                  </span>
                </div>
              )}
            </div>

            {hasChanges && (
              <button
                onClick={resetRoster}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                  text-xs font-medium text-zinc-300
                  border border-zinc-700 hover:border-zinc-500
                  bg-zinc-900/50 hover:bg-zinc-800/70
                  transition-all duration-150"
              >
                ↺ Reset
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="px-4 md:px-10 py-10 max-w-screen-2xl mx-auto">

        {/* ── 1. cap ────────────────────────────────────────────────────────── */}
        <Section
          title="Cap Summary"
          sub={hasChanges
            ? `Reflecting scenario changes · base was $${cap ? (cap.committed / 1e6).toFixed(1) : '—'}M`
            : 'Cap figures estimated · verify against NBPA memo when released'}
          badge="2026-27"
        >
          {cLoad
            ? <div className="h-48 rounded-xl bg-zinc-900/40 animate-pulse" />
            : computedCap && <CapBar cap={computedCap} />
          }
        </Section>

        {/* ── 2. roster ─────────────────────────────────────────────────────── */}
        <Section
          title="2026-27 Roster"
          sub="Stats from 2025-26 · click any column header to sort"
          badge={`${workingRoster.length} players`}
        >
          {rLoad
            ? <div className="h-48 rounded-xl bg-zinc-900/40 animate-pulse" />
            : (
              <StatTable
                rows={workingRoster}
                cols={ROSTER_COLS}
                rowKey={r => `${r.id}-${signingIds.has(r.id) ? 's' : 'o'}`}
                highlight={r =>
                  signingIds.has(r.id)
                    ? 'bg-indigo-950/30'
                    : r.years_left === 0
                    ? 'bg-amber-950/30'
                    : (r.years_left ?? 99) >= 3
                    ? 'bg-emerald-950/20'
                    : ''
                }
                renderActions={r =>
                  signingIds.has(r.id) ? (
                    <button
                      onClick={() => unsignPlayer(r.id)}
                      className="px-2 py-0.5 text-[10px] rounded border border-zinc-700
                        text-zinc-500 hover:border-zinc-500 hover:text-zinc-300
                        transition-colors whitespace-nowrap"
                    >
                      Undo
                    </button>
                  ) : (
                    <button
                      onClick={() => removePlayer(r.id)}
                      className="px-2 py-0.5 text-[10px] rounded border border-transparent
                        text-zinc-700 hover:border-red-800 hover:text-red-400
                        transition-colors whitespace-nowrap"
                    >
                      Release
                    </button>
                  )
                }
              />
            )
          }

          <div className="mt-3 flex flex-wrap gap-4 text-[10px] text-zinc-600">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm bg-amber-950/80 border border-amber-800/40" />
              Expiring
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm bg-emerald-950/60 border border-emerald-800/30" />
              Locked 3+ yrs
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm bg-indigo-950/60 border border-indigo-800/30" />
              Signed from FA pool
            </span>
            <span>PO = player option · TO = team option</span>
          </div>
        </Section>

        {/* ── 3. FA pool ────────────────────────────────────────────────────── */}
        <Section
          title="2027 Free Agent Pool"
          sub="League-wide · contracts expiring after 2026-27 · Stats from 2025-26"
          badge={fas ? `${fas.length} players` : undefined}
        >
          <div className="flex flex-wrap gap-3 mb-5 items-center">
            <FilterSelect label="Min GP" value={minGP} onChange={v => setMinGP(Number(v))}>
              {[0, 10, 20, 30, 41].map(n => (
                <option key={n} value={n}>{n === 0 ? 'All GPs' : `${n}+ GP`}</option>
              ))}
            </FilterSelect>

            <FilterSelect label="Position" value={pos} onChange={setPos}>
              <option value="">All</option>
              <option value="G">Guards</option>
              <option value="F">Forwards</option>
              <option value="C">Centers</option>
              <option value="PG">PG</option>
              <option value="SG">SG</option>
              <option value="SF">SF</option>
              <option value="PF">PF</option>
            </FilterSelect>

            <FilterSelect label="Sort by" value={sortBy} onChange={setSortBy}>
              <option value="bpm">BPM</option>
              <option value="vorp">VORP</option>
              <option value="e_net_rating">E_NET</option>
              <option value="pts">Points</option>
              <option value="pts_per_75">Pts / 75</option>
              <option value="ts_pct">TS%</option>
              <option value="mpg">Minutes</option>
            </FilterSelect>

            {signings.length > 0 && (
              <span className="text-[11px] text-indigo-400 ml-auto">
                {signings.length} added to roster
              </span>
            )}
          </div>

          {fLoad
            ? <div className="h-64 rounded-xl bg-zinc-900/40 animate-pulse" />
            : fas && (
              <StatTable
                rows={fas}
                cols={FA_COLS}
                rowKey={r => r.id}
                highlight={r => signingIds.has(r.id) ? 'opacity-40' : ''}
                renderActions={r =>
                  signingIds.has(r.id) ? (
                    <span className="text-[10px] text-emerald-400 font-semibold tracking-wide">
                      ✓ Signed
                    </span>
                  ) : (
                    <ShimmerButton
                      onClick={() => setSignTarget(r)}
                      background="linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)"
                      className="px-3 py-1 text-[10px] leading-none"
                    >
                      Sign
                    </ShimmerButton>
                  )
                }
              />
            )
          }
        </Section>
      </main>
    </div>
  )
}
