import type { ReactNode, CSSProperties } from 'react'
import { cn } from '../../lib/utils'

interface Props {
  children: ReactNode
  className?: string
}

export function AnimatedGradientText({ children, className }: Props) {
  return (
    <span
      style={
        {
          '--bg-size': '300%',
          background: 'linear-gradient(90deg, #e2e8f0 0%, #a5b4fc 30%, #38bdf8 50%, #a5b4fc 70%, #e2e8f0 100%)',
          backgroundSize: 'var(--bg-size) 100%',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        } as CSSProperties
      }
      className={cn('animate-gradient inline-block', className)}
    >
      {children}
    </span>
  )
}
