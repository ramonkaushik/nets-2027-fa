import { useEffect, useState } from 'react'

declare const __API_BASE__: string
// __API_BASE__ is injected by Vite at build time (vite.config.ts define block).
// Falls back to '' so relative paths work both in dev and when the API is
// co-located with the frontend (e.g. the Next.js portfolio deployment).
const API_BASE = typeof __API_BASE__ !== 'undefined' ? __API_BASE__ : ''

export function useApi<T>(path: string): { data: T | null; loading: boolean; error: string | null } {
  const [data, setData]       = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    fetch(`${API_BASE}${path}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(String(e)); setLoading(false) })
  }, [path])

  return { data, loading, error }
}
