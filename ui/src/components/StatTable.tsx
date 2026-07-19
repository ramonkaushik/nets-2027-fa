import { useState } from 'react'
import { cn } from '../lib/utils'

export interface ColDef<T> {
  key: keyof T
  label: string
  title?: string
  fmt?: (v: unknown) => string
  align?: 'left' | 'right'
  sticky?: boolean
}

interface Props<T> {
  rows: T[]
  cols: ColDef<T>[]
  rowKey: (row: T) => string | number
  highlight?: (row: T) => string
  renderActions?: (row: T) => React.ReactNode
}

const fmtDefault = (v: unknown): string => {
  if (v == null) return '—'
  if (typeof v === 'number') return v % 1 === 0 ? String(v) : v.toFixed(1)
  return String(v)
}

export function StatTable<T>({ rows, cols, rowKey, highlight, renderActions }: Props<T>) {
  const [sortKey, setSortKey] = useState<keyof T | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  // Null values sort last in both directions — -Infinity pushes them to the
  // bottom whether we're going desc (best first) or asc (worst first).
  const sorted = sortKey
    ? [...rows].sort((a, b) => {
        const av = a[sortKey] ?? -Infinity
        const bv = b[sortKey] ?? -Infinity
        return sortDir === 'desc'
          ? (bv as number) - (av as number)
          : (av as number) - (bv as number)
      })
    : rows

  const toggleSort = (key: keyof T) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-zinc-900/40 backdrop-blur-sm">
      <table className="text-xs w-full border-collapse">
        <thead>
          <tr className="border-b border-white/[0.06]">
            {cols.map(col => (
              <th
                key={String(col.key)}
                title={col.title ?? String(col.key)}
                onClick={() => toggleSort(col.key)}
                className={cn(
                  'px-3 py-2.5 font-medium whitespace-nowrap cursor-pointer select-none',
                  'text-[10px] uppercase tracking-widest',
                  'transition-colors duration-150',
                  'text-zinc-500 hover:text-zinc-200',
                  col.align === 'left' ? 'text-left' : 'text-right',
                  col.sticky ? 'sticky left-0 z-10 bg-zinc-900/90 backdrop-blur-sm' : '',
                  sortKey === col.key ? 'text-indigo-400' : '',
                )}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className="ml-1 opacity-80">{sortDir === 'desc' ? '↓' : '↑'}</span>
                )}
              </th>
            ))}
            {renderActions && (
              <th className={cn(
                'px-3 py-2.5 sticky right-0 z-10',
                'bg-zinc-900/90 backdrop-blur-sm border-l border-white/[0.04]',
              )} />
            )}
          </tr>
        </thead>
        <tbody>
          {sorted.map(row => (
            <tr
              key={rowKey(row)}
              className={cn(
                'group border-t border-white/[0.04]',
                'transition-colors duration-100',
                'hover:bg-white/[0.03]',
                highlight ? highlight(row) : '',
              )}
            >
              {cols.map(col => {
                const val = row[col.key]
                const fmt = col.fmt ?? fmtDefault
                return (
                  <td
                    key={String(col.key)}
                    className={cn(
                      'px-3 py-2 whitespace-nowrap',
                      col.align === 'left' ? 'text-left' : 'text-right',
                      col.sticky
                        ? 'sticky left-0 z-10 bg-zinc-900/90 backdrop-blur-sm group-hover:bg-zinc-800/60'
                        : '',
                      val == null ? 'text-zinc-700' : 'text-zinc-300',
                    )}
                  >
                    {fmt(val)}
                  </td>
                )
              })}
              {renderActions && (
                <td className={cn(
                  'px-3 py-2 text-right sticky right-0 z-10',
                  'bg-zinc-900/90 backdrop-blur-sm group-hover:bg-zinc-800/60',
                  'border-l border-white/[0.04]',
                )}>
                  {renderActions(row)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
