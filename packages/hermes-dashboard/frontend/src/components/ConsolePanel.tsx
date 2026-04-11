import { useEffect, useState } from 'react'
import { useApi } from '../hooks/useApi'
import Panel from './Panel'

type ConsoleSession = {
  id: string
  cwd: string
  terminal_url: string
  ready: boolean
}

type ConsoleData = {
  session: ConsoleSession | null
}

async function postJson(path: string) {
  const response = await fetch(path, { method: 'POST' })
  if (!response.ok) {
    throw new Error(await response.text())
  }
  return response.json()
}

export default function ConsolePanel() {
  const { data, isLoading, mutate } = useApi<ConsoleData>('/console', 3000)
  const [pending, setPending] = useState<'open' | 'close' | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isLoading || pending || data?.session) {
      return
    }

    let cancelled = false
    setPending('open')
    postJson('/api/console/open')
      .then((payload) => {
        if (!cancelled) {
          setError(null)
          void mutate(payload, { revalidate: false })
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setPending(null)
        }
      })

    return () => {
      cancelled = true
    }
  }, [data?.session, isLoading, mutate, pending])

  const session = data?.session ?? null

  const closeSession = async () => {
    if (!session) {
      return
    }
    setPending('close')
    try {
      const payload = await postJson(`/api/console/sessions/${session.id}/close`)
      setError(null)
      await mutate(payload, { revalidate: false })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setPending(null)
    }
  }

  return (
    <Panel title="Console" className="col-span-full">
      <div className="flex items-center justify-between gap-3 mb-3 text-[13px]">
        <div style={{ color: 'var(--hud-text-dim)' }}>
          {session ? session.cwd : '/workspace'}
        </div>
        <div className="flex items-center gap-2">
          {session && (
            <span style={{ color: session.ready ? 'var(--hud-success)' : 'var(--hud-warning)' }}>
              {session.ready ? 'LIVE' : 'STARTING'}
            </span>
          )}
          <button
            type="button"
            onClick={closeSession}
            disabled={!session || pending === 'close'}
            className="px-2 py-1 border text-[13px]"
            style={{
              borderColor: 'var(--hud-border)',
              color: !session ? 'var(--hud-text-dim)' : 'var(--hud-text)',
              opacity: pending === 'close' ? 0.6 : 1,
            }}
          >
            {pending === 'close' ? 'Closing...' : 'Close'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-3 text-[13px]" style={{ color: 'var(--hud-error)' }}>
          {error}
        </div>
      )}

      {(!session || pending === 'open') && (
        <div className="text-[13px] animate-pulse" style={{ color: 'var(--hud-text-dim)' }}>
          Starting console...
        </div>
      )}

      {session && (
        <div className="border" style={{ borderColor: 'var(--hud-border)', minHeight: '70vh' }}>
          <iframe
            key={session.id}
            src={session.terminal_url}
            title="Console"
            className="w-full"
            style={{ minHeight: '70vh', background: '#000' }}
          />
        </div>
      )}
    </Panel>
  )
}
