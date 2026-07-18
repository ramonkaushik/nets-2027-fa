import { useEffect, useState } from 'react'

declare const __API_BASE__: string
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
