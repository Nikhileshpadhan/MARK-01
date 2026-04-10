import { useMemo } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useRankingQuery, useRefreshMutation } from '../hooks/useDashboardData'
import RefreshButton from '../components/RefreshButton'
import { formatTimestamp } from '../utils/format'

const navLinkClass = ({ isActive }) =>
  `rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors duration-200 ${
    isActive
      ? 'bg-primary-container text-white'
      : 'text-onSurface-variant hover:bg-surface-container-high hover:text-onSurface'
  }`

export default function DashboardLayout({ children }) {
  const location = useLocation()
  const isDashboardView = location.pathname.startsWith('/dashboard') || location.pathname.startsWith('/company/')

  const rankingQuery = useRankingQuery({ enabled: isDashboardView })
  const refreshMutation = useRefreshMutation()

  const lastUpdated = useMemo(() => {
    const rows = rankingQuery.data || []
    if (!rows.length) {
      return null
    }
    return rows[0].timestamp
  }, [rankingQuery.data])

  return (
    <div className="min-h-screen bg-surface text-onSurface">
      <header className="fixed inset-x-0 top-0 z-30 bg-surface/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-3.5 md:px-8">
          <div className="flex items-center gap-8">
            <NavLink to="/" className="group">
              <h1 className="text-lg font-semibold tracking-tight text-onSurface">MarketMind</h1>
            </NavLink>
            <nav className="hidden items-center gap-1 md:flex">
              <NavLink to="/" end className={navLinkClass}>Home</NavLink>
              <NavLink to="/dashboard" className={navLinkClass}>Rankings</NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            {isDashboardView && lastUpdated && (
              <p className="hidden text-xs text-onSurface-variant md:block">
                Updated {formatTimestamp(lastUpdated)}
              </p>
            )}
            {isDashboardView ? (
              <RefreshButton onClick={() => refreshMutation.mutate()} isLoading={refreshMutation.isPending} />
            ) : (
              <NavLink
                to="/dashboard"
                className="rounded-full bg-primary-container px-5 py-2 text-sm font-medium text-white transition-colors duration-200 hover:bg-primary-container/80"
              >
                Open Rankings
              </NavLink>
            )}
          </div>
        </div>

        {/* Mobile nav */}
        <div className="mx-auto flex w-full max-w-7xl items-center gap-1 px-5 pb-3 md:hidden">
          <NavLink to="/" end className={navLinkClass}>Home</NavLink>
          <NavLink to="/dashboard" className={navLinkClass}>Rankings</NavLink>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-5 pb-24 pt-28 md:px-8">{children}</main>

      <footer className="px-5 py-8 text-center text-xs text-onSurface-variant/60">
        MarketMind Analytics Platform
      </footer>
    </div>
  )
}
