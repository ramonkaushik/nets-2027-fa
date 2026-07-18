import type { CapSummary } from '../types'
import { NumberTicker } from './magicui/NumberTicker'
import { BorderBeam } from './magicui/BorderBeam'
import { MagicCard } from './magicui/MagicCard'

const M = (n: number) => (n / 1e6).toFixed(1)

interface CardProps {
  label: string
  value: number
  sub: string
  warn?: boolean
  accent?: boolean
  beam?: boolean
}

function StatCard({ label, value, sub, warn, accent, beam }: CardProps) {
  const absM = Math.abs(value) / 1e6
  const neg  = value < 0

  return (
    <MagicCard
      gradientColor={warn ? 'rgba(239,68,68,0.12)' : accent ? 'rgba(99,102,241,0.15)' : 'rgba(100,80,200,0.1)'}
      className={`relative rounded-xl border p-4 transition-colors duration-200
        ${warn
          ? 'border-red-500/30 bg-red-950/20'
          : accent
          ? 'border-indigo-500/30 bg-indigo-950/20'
          : 'border-zinc-800 bg-zinc-900/60'
        }`}
    >
      {beam && <BorderBeam colorFrom="#a78bfa" colorTo="#38bdf8" duration={8} />}
      <div className="text-[11px] uppercase tracking-widest text-zinc-500 mb-2 font-medium">{label}</div>
      <div className={`text-2xl font-bold tabular-nums
        ${warn ? 'text-red-400' : accent ? 'text-indigo-300' : 'text-white'}`}>
        {neg ? '-' : ''}$<NumberTicker value={absM} decimals={1} suffix="M" />
      </div>
      <div className={`text-[11px] mt-1 ${warn ? 'text-red-500/80' : 'text-zinc-500'}`}>{sub}</div>
    </MagicCard>
  )
}

export function CapBar({ cap }: { cap: CapSummary }) {
  const max = cap.second_apron * 1.06
  const pct = (n: number) => `${Math.min((n / max) * 100, 100).toFixed(2)}%`

  const thresholds = [
    { val: cap.salary_cap,   label: 'Cap',       color: '#22c55e',  glow: '#22c55e40' },
    { val: cap.tax_line,     label: 'Tax',        color: '#eab308',  glow: '#eab30840' },
    { val: cap.first_apron,  label: '1st Apron', color: '#f97316',  glow: '#f9731640' },
    { val: cap.second_apron, label: '2nd Apron', color: '#ef4444',  glow: '#ef444440' },
  ]

  const overTax    = cap.committed > cap.tax_line
  const overApron1 = cap.committed > cap.first_apron
  const overApron2 = cap.committed > cap.second_apron

  return (
    <div className="space-y-6">
      {/* bar */}
      <div className="relative mt-8">
        <div className="relative h-7 rounded-full bg-zinc-800/80 overflow-visible border border-zinc-700/50">
          {/* fill */}
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
            style={{
              width: pct(cap.committed),
              background: overApron2
                ? 'linear-gradient(90deg, #4f46e5, #dc2626)'
                : overApron1
                ? 'linear-gradient(90deg, #4f46e5, #ea580c)'
                : overTax
                ? 'linear-gradient(90deg, #4f46e5, #ca8a04)'
                : 'linear-gradient(90deg, #4f46e5, #6366f1)',
              boxShadow: overTax
                ? '0 0 16px rgba(239,68,68,0.3)'
                : '0 0 16px rgba(99,102,241,0.3)',
            }}
          />

          {/* threshold lines */}
          {thresholds.map(({ val, label, color, glow }) => (
            <div
              key={label}
              className="absolute top-0 h-full flex flex-col items-center"
              style={{ left: pct(val) }}
            >
              <div
                className="w-px h-full"
                style={{ background: color, boxShadow: `0 0 6px ${glow}` }}
              />
              <span
                className="absolute -top-6 text-[10px] font-semibold whitespace-nowrap translate-x-1"
                style={{ color }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>

        {/* committed label */}
        <div
          className="absolute -bottom-5 text-[10px] text-zinc-400 whitespace-nowrap"
          style={{ left: pct(cap.committed), transform: 'translateX(-50%)' }}
        >
          ${M(cap.committed)}M
        </div>
      </div>

      {/* cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
        <StatCard
          label="Committed"
          value={cap.committed}
          sub={`of $${M(cap.salary_cap)}M cap`}
          accent
          beam
        />
        <StatCard
          label="Expiring"
          value={cap.expiring}
          sub="coming off books"
        />
        <StatCard
          label="2027 Floor"
          value={cap.projected_next}
          sub="min committed next yr"
        />
        <StatCard
          label="Room to Tax"
          value={cap.room_to_tax}
          sub={cap.room_to_tax >= 0 ? 'below tax line' : 'OVER tax line'}
          warn={cap.room_to_tax < 0}
        />
      </div>
    </div>
  )
}
