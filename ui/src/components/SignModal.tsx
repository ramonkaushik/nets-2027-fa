import { useState } from 'react'
import type { FreeAgent } from '../types'
import { ShimmerButton } from './magicui/ShimmerButton'
import { BorderBeam } from './magicui/BorderBeam'

interface Props {
  player: FreeAgent
  onConfirm: (salary: number, years: number) => void
  onCancel: () => void
}

export function SignModal({ player, onConfirm, onCancel }: Props) {
  const [salaryM, setSalaryM] = useState('')
  const [years,   setYears]   = useState('2')

  // Input is in $M (e.g. "12.5") — convert to whole dollars for the cap math.
  const salary = parseFloat(salaryM) * 1_000_000
  const valid  = !isNaN(salary) && salary > 0 && parseInt(years) >= 1

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(12px)' }}
    >
      <div
        className="relative w-84 rounded-2xl border border-white/10 p-6 shadow-2xl"
        style={{
          background: 'linear-gradient(145deg, rgba(24,24,27,0.95) 0%, rgba(15,15,20,0.98) 100%)',
          boxShadow: '0 0 60px rgba(99,102,241,0.15), 0 25px 50px rgba(0,0,0,0.6)',
        }}
      >
        <BorderBeam colorFrom="#a78bfa" colorTo="#38bdf8" duration={6} borderWidth={1} />

        {/* header */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-widest text-indigo-400 font-semibold">Sign free agent</span>
          </div>
          <div className="text-xl font-bold text-white">{player.name}</div>
          <div className="text-xs text-zinc-400 mt-0.5 flex flex-wrap gap-x-2">
            <span>{player.position}</span>
            <span className="text-zinc-600">·</span>
            <span>{player.prior_team}</span>
            <span className="text-zinc-600">·</span>
            <span>{player.fa_type}</span>
            {player.pts != null && (
              <>
                <span className="text-zinc-600">·</span>
                <span>{player.pts.toFixed(1)} pts</span>
              </>
            )}
            {player.bpm != null && (
              <>
                <span className="text-zinc-600">·</span>
                <span className={player.bpm >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                  BPM {player.bpm > 0 ? '+' : ''}{player.bpm.toFixed(1)}
                </span>
              </>
            )}
          </div>
        </div>

        {/* inputs */}
        <div className="space-y-3 mb-5">
          <div>
            <label className="block text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">Annual salary</label>
            <div className="flex items-center gap-1.5">
              <span className="text-zinc-400 text-sm font-medium">$</span>
              <input
                type="number"
                min="0"
                step="0.5"
                placeholder="e.g. 12.5"
                value={salaryM}
                onChange={e => setSalaryM(e.target.value)}
                className="flex-1 rounded-lg px-3 py-2 text-sm text-white
                  border border-zinc-700 focus:border-indigo-500
                  bg-zinc-900/80 focus:outline-none focus:ring-1 focus:ring-indigo-500/50
                  transition-colors placeholder:text-zinc-600"
                autoFocus
              />
              <span className="text-zinc-400 text-sm font-medium">M</span>
            </div>
          </div>

          <div>
            <label className="block text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">Years</label>
            <input
              type="number"
              min="1"
              max="5"
              value={years}
              onChange={e => setYears(e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-sm text-white
                border border-zinc-700 focus:border-indigo-500
                bg-zinc-900/80 focus:outline-none focus:ring-1 focus:ring-indigo-500/50
                transition-colors"
            />
          </div>
        </div>

        {/* actions */}
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="flex-1 rounded-lg border border-zinc-700 px-3 py-2
              text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <ShimmerButton
            onClick={() => valid && onConfirm(salary, parseInt(years))}
            disabled={!valid}
            className="flex-1 py-2"
          >
            Add to Roster →
          </ShimmerButton>
        </div>
      </div>
    </div>
  )
}
