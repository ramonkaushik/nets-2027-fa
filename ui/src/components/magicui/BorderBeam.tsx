import type { CSSProperties } from 'react'
import { cn } from '../../lib/utils'

interface Props {
  className?: string
  size?: number
  duration?: number
  colorFrom?: string
  colorTo?: string
  delay?: number
  borderWidth?: number
}

export function BorderBeam({
  className,
  size       = 180,
  duration   = 12,
  colorFrom  = '#a78bfa',
  colorTo    = '#38bdf8',
  delay      = 0,
  borderWidth = 1,
}: Props) {
  return (
    <div
      style={{
        '--size':         size,
        '--duration':     duration,
        '--color-from':   colorFrom,
        '--color-to':     colorTo,
        '--delay':        `-${delay}s`,
        '--border-width': borderWidth,
      } as CSSProperties}
      className={cn(
        'pointer-events-none absolute inset-0 rounded-[inherit]',
        '[border:calc(var(--border-width)*1px)_solid_transparent]',
        '![mask-clip:padding-box,border-box]',
        '![mask-composite:intersect]',
        '[mask:linear-gradient(transparent,transparent),linear-gradient(white,white)]',
        'after:absolute after:aspect-square',
        'after:w-[calc(var(--size)*1px)]',
        'after:animate-border-beam',
        'after:[animation-delay:var(--delay)]',
        'after:[animation-duration:calc(var(--duration)*1s)]',
        'after:[background:linear-gradient(to_left,var(--color-from),var(--color-to),transparent)]',
        'after:[offset-anchor:calc(var(--anchor,90)*1%)_50%]',
        'after:[offset-path:rect(0_auto_auto_0_round_8px)]',
        className,
      )}
    />
  )
}
