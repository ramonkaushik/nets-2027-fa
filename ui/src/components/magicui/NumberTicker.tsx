import { useEffect, useRef } from 'react'
import { useInView, useMotionValue, useSpring } from 'framer-motion'
import { cn } from '../../lib/utils'

interface Props {
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
  className?: string
  delay?: number
}

export function NumberTicker({ value, decimals = 0, prefix = '', suffix = '', className, delay = 0 }: Props) {
  const ref     = useRef<HTMLSpanElement>(null)
  const mv      = useMotionValue(0)
  const spring  = useSpring(mv, { damping: 60, stiffness: 100 })
  const inView  = useInView(ref, { once: true })

  useEffect(() => {
    if (inView) {
      const t = setTimeout(() => mv.set(value), delay * 1000)
      return () => clearTimeout(t)
    }
  }, [inView, value, mv, delay])

  useEffect(() => spring.on('change', (v) => {
    if (ref.current) {
      ref.current.textContent =
        prefix +
        Intl.NumberFormat('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(
          parseFloat(v.toFixed(decimals))
        ) +
        suffix
    }
  }), [spring, decimals, prefix, suffix])

  return (
    <span
      ref={ref}
      className={cn('tabular-nums', className)}
    />
  )
}
