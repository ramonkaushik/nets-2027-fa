import { useCallback, useRef, type ReactNode, type CSSProperties } from 'react'
import { cn } from '../../lib/utils'

interface Props {
  children: ReactNode
  className?: string
  gradientColor?: string
  gradientSize?: number
}

export function MagicCard({
  children,
  className,
  gradientColor = 'rgba(100,80,200,0.15)',
  gradientSize  = 280,
}: Props) {
  const cardRef = useRef<HTMLDivElement>(null)
  const spotRef = useRef<HTMLDivElement>(null)

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!cardRef.current || !spotRef.current) return
    const { left, top } = cardRef.current.getBoundingClientRect()
    const x = e.clientX - left
    const y = e.clientY - top
    spotRef.current.style.background =
      `radial-gradient(${gradientSize}px circle at ${x}px ${y}px, ${gradientColor}, transparent 70%)`
    spotRef.current.style.opacity = '1'
  }, [gradientColor, gradientSize])

  const handleMouseLeave = useCallback(() => {
    if (spotRef.current) spotRef.current.style.opacity = '0'
  }, [])

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={cn('relative overflow-hidden', className)}
      style={{ '--gradient-color': gradientColor } as CSSProperties}
    >
      <div
        ref={spotRef}
        className="pointer-events-none absolute inset-0 transition-opacity duration-300"
        style={{ opacity: 0 }}
      />
      {children}
    </div>
  )
}
