import { cn } from '../../lib/utils'

interface Props {
  number?: number
  className?: string
}

export function Meteors({ number = 16, className }: Props) {
  const meteors = Array.from({ length: number }, (_, i) => ({
    id: i,
    left: `${Math.floor(Math.random() * 100)}%`,
    delay: `${Math.random() * 8}s`,
    duration: `${Math.floor(Math.random() * 6) + 4}s`,
    size: `${Math.floor(Math.random() * 80) + 40}px`,
  }))

  return (
    <>
      {meteors.map(({ id, left, delay, duration, size }) => (
        <span
          key={id}
          className={cn(
            'pointer-events-none absolute top-0 rotate-[215deg] animate-meteor',
            'h-px rounded-full',
            'bg-linear-to-r from-zinc-400 via-zinc-300/60 to-transparent',
            'shadow-[0_0_0_1px_#ffffff08]',
            className,
          )}
          style={{
            left,
            width: size,
            animationDelay: delay,
            animationDuration: duration,
          }}
        />
      ))}
    </>
  )
}
