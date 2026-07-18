import type { CSSProperties, ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface Props {
  children: ReactNode
  className?: string
  shimmerColor?: string
  background?: string
  onClick?: () => void
  disabled?: boolean
  type?: 'button' | 'submit'
}

export function ShimmerButton({
  children,
  className,
  shimmerColor = 'rgba(255,255,255,0.15)',
  background   = 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)',
  onClick,
  disabled,
  type = 'button',
}: Props) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{ '--shimmer-color': shimmerColor, background } as CSSProperties}
      className={cn(
        'group relative overflow-hidden rounded-lg px-4 py-2',
        'text-sm font-semibold text-white',
        'transition-all duration-300 ease-out',
        'hover:scale-[1.02] active:scale-[0.98]',
        'disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100',
        'shadow-lg shadow-indigo-950/50',
        className,
      )}
    >
      {/* shimmer layer */}
      <span
        className={cn(
          'absolute inset-0 -translate-x-full',
          'bg-[linear-gradient(90deg,transparent_0%,var(--shimmer-color)_50%,transparent_100%)]',
          'bg-[length:200%_100%]',
          'animate-shimmer',
          'group-disabled:hidden',
        )}
      />
      <span className="relative z-10">{children}</span>
    </button>
  )
}
