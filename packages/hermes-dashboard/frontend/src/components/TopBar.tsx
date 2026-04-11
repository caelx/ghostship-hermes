import { useState, useEffect } from 'react'
import { useTheme, THEMES } from '../hooks/useTheme'

export const TABS = [
  { id: 'dashboard', label: 'Dashboard', key: '1' },
  { id: 'memory', label: 'Memory', key: '2' },
  { id: 'skills', label: 'Skills', key: '3' },
  { id: 'sessions', label: 'Sessions', key: '4' },
  { id: 'cron', label: 'Cron', key: '5' },
  { id: 'projects', label: 'Projects', key: '6' },
  { id: 'health', label: 'Health', key: '7' },
  { id: 'agents', label: 'Agents', key: '8' },
  { id: 'profiles', label: 'Profiles', key: '9' },
  { id: 'token-costs', label: 'Costs', key: '0' },
  { id: 'console', label: 'Console', key: 'C' },
] as const

export type TabId = typeof TABS[number]['id']

interface TopBarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

export default function TopBar({ activeTab, onTabChange }: TopBarProps) {
  const { theme, setTheme, scanlines, setScanlines } = useTheme()
  const [showThemePicker, setShowThemePicker] = useState(false)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
      if (e.metaKey || e.ctrlKey || e.altKey) return

      const num = parseInt(e.key)
      if (!Number.isNaN(num) && num >= 1 && num <= 9) {
        onTabChange(TABS[num - 1].id)
        return
      }
      if (e.key === '0') {
        onTabChange('token-costs')
        return
      }
      if (e.key.toLowerCase() === 'c') {
        onTabChange('console')
        return
      }
      if (e.key === 't') {
        setShowThemePicker((p) => !p)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onTabChange])

  return (
    <div className="flex items-center gap-1 px-3 py-1.5 border-b" style={{ borderColor: 'var(--hud-border)', background: 'var(--hud-bg-surface)' }}>
      <span className="gradient-text font-bold text-[13px] mr-3 tracking-wider cursor-pointer shrink-0" onClick={() => onTabChange('dashboard')}>
        HERMES
      </span>

      <div className="flex gap-0.5 flex-1 overflow-x-auto" style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className="px-2 py-1.5 text-[13px] tracking-widest uppercase transition-all duration-150 shrink-0 cursor-pointer"
            style={{
              color: activeTab === tab.id ? 'var(--hud-primary)' : 'var(--hud-text-dim)',
              background: activeTab === tab.id ? 'var(--hud-bg-panel)' : 'transparent',
              borderBottom: activeTab === tab.id ? '2px solid var(--hud-primary)' : '2px solid transparent',
              textShadow: activeTab === tab.id ? '0 0 8px var(--hud-primary-glow)' : 'none',
              minHeight: '32px',
            }}
          >
            <span className="opacity-40 mr-1">{tab.key}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="relative shrink-0">
        <button
          onClick={() => setShowThemePicker((p) => !p)}
          className="px-2 py-1.5 text-[13px] tracking-wider uppercase cursor-pointer"
          style={{ color: 'var(--hud-text-dim)', minHeight: '32px' }}
          title="Theme (t)"
        >
          Theme
        </button>
        {showThemePicker && (
          <div className="absolute right-0 top-full mt-1 z-50 py-1 min-w-[180px]" style={{ background: 'var(--hud-bg-panel)', border: '1px solid var(--hud-border)', boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }}>
            {THEMES.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setTheme(item.id)
                  setShowThemePicker(false)
                }}
                className="block w-full text-left px-3 py-2 text-[13px] transition-colors cursor-pointer"
                style={{
                  color: theme === item.id ? 'var(--hud-primary)' : 'var(--hud-text)',
                  background: theme === item.id ? 'var(--hud-bg-hover)' : 'transparent',
                  minHeight: '36px',
                }}
              >
                {item.icon} {item.label}
              </button>
            ))}
            <div className="border-t my-1" style={{ borderColor: 'var(--hud-border)' }} />
            <button
              onClick={() => setScanlines(!scanlines)}
              className="block w-full text-left px-3 py-2 text-[13px] cursor-pointer"
              style={{ color: 'var(--hud-text-dim)', minHeight: '36px' }}
            >
              {scanlines ? 'On' : 'Off'} scanlines
            </button>
          </div>
        )}
      </div>

      <span className="text-[13px] ml-2 tabular-nums shrink-0 hidden sm:inline" style={{ color: 'var(--hud-text-dim)' }}>
        {time.toLocaleTimeString('en-US', { hour12: false })}
      </span>
    </div>
  )
}
