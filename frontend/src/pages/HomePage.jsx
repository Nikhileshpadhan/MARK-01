import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import MobileRankingCards from '../components/MobileRankingCards'
import RankingTable from '../components/RankingTable'
import SectorFilter from '../components/SectorFilter'
import SkeletonTable from '../components/SkeletonTable'
import { useRankingQuery } from '../hooks/useDashboardData'
import { searchCompanies } from '../lib/api'

export default function HomePage() {
  const navigate = useNavigate()
  const rankingQuery = useRankingQuery()
  const [activeSector, setActiveSector] = useState('All')
  const [searchTerm, setSearchTerm] = useState('')
  const [searchError, setSearchError] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const searchRef = useRef(null)
  const debounceRef = useRef(null)
  const rankingRows = rankingQuery.data || []
  const normalizedQuery = searchTerm.trim().toLowerCase()
  const shouldApplySearchFilter = normalizedQuery.length >= 3

  const sectors = useMemo(() => {
    const values = Array.from(new Set(rankingRows.map((row) => row.sector).filter(Boolean))).sort()
    return ['All', ...values]
  }, [rankingRows])

  const filteredRows = useMemo(() => {
    const sectorFiltered = activeSector === 'All' ? rankingRows : rankingRows.filter((row) => row.sector === activeSector)
    if (!shouldApplySearchFilter) {
      return sectorFiltered
    }
    return sectorFiltered.filter((row) => row.symbol.toLowerCase().includes(normalizedQuery) || row.name.toLowerCase().includes(normalizedQuery))
  }, [rankingRows, activeSector, normalizedQuery, shouldApplySearchFilter])

  const hasNoRankingData = rankingRows.length === 0
  const hasNoSearchMatches = !hasNoRankingData && shouldApplySearchFilter && filteredRows.length === 0

  // Debounced search for autocomplete
  const fetchSuggestions = useCallback(async (query) => {
    if (!query || query.trim().length < 1) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    try {
      const results = await searchCompanies(query)
      setSuggestions(results)
      setShowSuggestions(results.length > 0)
      setHighlightedIndex(-1)
    } catch {
      setSuggestions([])
      setShowSuggestions(false)
    }
  }, [])

  function handleSearchChange(event) {
    const value = event.target.value
    setSearchTerm(value)
    if (searchError) setSearchError('')

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 250)
  }

  function selectSuggestion(symbol) {
    setSearchTerm('')
    setSuggestions([])
    setShowSuggestions(false)
    setSearchError('')
    navigate(`/company/${symbol}`)
  }

  async function goToCompanyDashboard() {
    const query = searchTerm.trim().toUpperCase()
    if (!query) {
      setSearchError('')
      return
    }

    // Check suggestions first
    if (suggestions.length > 0) {
      const exactMatch = suggestions.find((s) => s.symbol.toUpperCase() === query)
      if (exactMatch) {
        selectSuggestion(exactMatch.symbol)
        return
      }
      // Use first suggestion
      selectSuggestion(suggestions[0].symbol)
      return
    }

    // Fallback: check ranking data
    const rows = rankingQuery.data || []
    const exactSymbol = rows.find((row) => row.symbol.toUpperCase() === query)
    if (exactSymbol) {
      selectSuggestion(exactSymbol.symbol)
      return
    }

    const nameMatch = rows.find((row) => row.name.toLowerCase() === query.toLowerCase())
    if (nameMatch) {
      selectSuggestion(nameMatch.symbol)
      return
    }

    // Final fallback: ask backend search (includes LLM ticker resolution for unknown companies)
    try {
      const remoteResults = await searchCompanies(query)
      if (remoteResults.length > 0) {
        selectSuggestion(remoteResults[0].symbol)
        return
      }
    } catch {
      // Keep existing user-friendly error below.
    }

    setSearchError('Company not found. Try a different symbol or name.')
  }

  function handleKeyDown(event) {
    if (!showSuggestions) {
      if (event.key === 'Enter') {
        void goToCompanyDashboard()
      }
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlightedIndex((prev) => Math.min(prev + 1, suggestions.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlightedIndex((prev) => Math.max(prev - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
        selectSuggestion(suggestions[highlightedIndex].symbol)
      } else {
        void goToCompanyDashboard()
      }
    } else if (event.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  // Close suggestions on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (rankingQuery.isLoading) {
    return <SkeletonTable />
  }

  if (rankingQuery.isError) {
    return (
      <section className="space-y-4">
        <div className="rounded-2xl bg-surface-container p-6">
          <h2 className="text-lg font-semibold text-negative">Unable to load rankings data</h2>
          <p className="mt-2 text-sm text-onSurface-variant">
            Check that backend is running on <span className="text-onSurface">{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</span> and then refresh.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="space-y-5">
      {/* Search with autocomplete */}
      <div className="rounded-2xl bg-surface-container p-5 md:p-6">
        <label htmlFor="company-search" className="text-[11px] font-medium uppercase tracking-widest text-onSurface-variant">
          Search company rankings
        </label>
        <div className="relative mt-3 flex flex-col gap-2.5 md:flex-row" ref={searchRef}>
          <div className="relative w-full">
            <input
              id="company-search"
              type="text"
              autoComplete="off"
              value={searchTerm}
              onChange={handleSearchChange}
              onKeyDown={handleKeyDown}
              onFocus={() => { if (suggestions.length > 0) setShowSuggestions(true) }}
              placeholder="Type symbol like AAPL or company name"
              className="w-full rounded-xl bg-surface-container-lowest px-4 py-2.5 text-sm text-onSurface outline-none placeholder:text-onSurface-variant/50 focus:ring-1 focus:ring-primary-container"
            />
            {/* Autocomplete dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute left-0 right-0 top-full z-50 mt-1 max-h-64 overflow-auto rounded-xl border border-surface-container-high bg-surface-container shadow-lg shadow-black/30">
                {suggestions.map((item, index) => (
                  <button
                    key={item.symbol}
                    type="button"
                    onClick={() => selectSuggestion(item.symbol)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                      index === highlightedIndex
                        ? 'bg-primary-container/15 text-onSurface'
                        : 'text-onSurface-variant hover:bg-surface-container-high'
                    }`}
                  >
                    <span className="min-w-[48px] font-semibold tabular-nums text-onSurface">{item.symbol}</span>
                    <span className="truncate text-onSurface-variant">{item.name}</span>
                    {item.sector && (
                      <span className="ml-auto shrink-0 rounded-full bg-surface-container-high px-2 py-0.5 text-[10px] font-medium text-onSurface-variant">
                        {item.sector}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={goToCompanyDashboard}
            className="shrink-0 rounded-xl bg-positive px-5 py-2.5 text-sm font-semibold text-surface transition-colors duration-200 hover:bg-positive/80"
          >
            Search
          </button>
        </div>
        {searchError ? <p className="mt-2 text-xs text-negative">{searchError}</p> : null}
      </div>

      <SectorFilter sectors={sectors} activeSector={activeSector} onSelect={setActiveSector} />

      {hasNoRankingData ? (
        <div className="rounded-2xl bg-surface-container p-6 text-onSurface-variant">
          No ranking data available yet. Trigger a backend refresh and try again.
        </div>
      ) : hasNoSearchMatches ? (
        <div className="rounded-2xl bg-surface-container p-6 text-onSurface-variant">
          No companies match this search yet. Try a different symbol or type at least 3 characters.
        </div>
      ) : (
        <>
          <MobileRankingCards rows={filteredRows} onSelect={(symbol) => navigate(`/company/${symbol}`)} />
          <div className="hidden md:block">
            <RankingTable rows={filteredRows} onSelect={(symbol) => navigate(`/company/${symbol}`)} />
          </div>
        </>
      )}
    </section>
  )
}
