import { useMemo, useState } from 'react'
import EngagementBadge from './EngagementBadge'
import PriceChange from './PriceChange'
import { formatNumber, formatPrice } from '../utils/format'

const ROW_HEIGHT = 52
const VIRTUAL_HEIGHT = 620

const columns = [
  { key: 'rank', label: 'Rank', width: 'w-[64px]', align: 'text-left' },
  { key: 'symbol', label: 'Symbol', width: 'w-[100px]', align: 'text-left' },
  { key: 'name', label: 'Company', width: 'min-w-[180px] flex-1', align: 'text-left' },
  { key: 'price', label: 'Price', width: 'w-[110px]', align: 'text-right' },
  { key: 'change', label: 'Change', width: 'w-[110px]', align: 'text-right' },
  { key: 'engagement', label: 'Engagement', width: 'w-[130px]', align: 'text-center' },
  { key: 'score', label: 'Score', width: 'w-[90px]', align: 'text-right' },
]

function HeaderRow() {
  return (
    <div className="flex items-center border-b border-outline-variant/10 px-4 py-3">
      {columns.map((col) => (
        <div key={col.key} className={`${col.width} ${col.align} text-[11px] font-medium uppercase tracking-wider text-onSurface-variant`}>
          {col.label}
        </div>
      ))}
    </div>
  )
}

function DataRow({ row, onSelect }) {
  const score = Number(row.final_score ?? 0)
  return (
    <button
      type="button"
      onClick={() => onSelect(row.symbol)}
      className="flex w-full items-center px-4 text-left transition-colors duration-200 hover:bg-surface-container-high"
      style={{ height: ROW_HEIGHT }}
    >
      <div className={`${columns[0].width} ${columns[0].align} text-sm text-onSurface-variant`}>#{row.rank}</div>
      <div className={`${columns[1].width} ${columns[1].align} text-sm font-semibold text-onSurface`}>{row.symbol}</div>
      <div className={`${columns[2].width} ${columns[2].align} truncate pr-4 text-sm text-onSurface-variant`}>{row.name}</div>
      <div className={`${columns[3].width} ${columns[3].align} text-sm tabular-nums text-onSurface`}>{formatPrice(row.price)}</div>
      <div className={`${columns[4].width} ${columns[4].align}`}><PriceChange value={row.change_percent} /></div>
      <div className={`${columns[5].width} ${columns[5].align}`}><EngagementBadge count={row.mention_count} /></div>
      <div className={`${columns[6].width} ${columns[6].align} text-sm font-semibold tabular-nums text-positive`}>{score.toFixed(2)}</div>
    </button>
  )
}

export default function RankingTable({ rows, onSelect }) {
  const [scrollTop, setScrollTop] = useState(0)
  const useVirtual = rows.length > 100

  const virtualState = useMemo(() => {
    if (!useVirtual) {
      return { visibleRows: rows, topSpace: 0, totalHeight: rows.length * ROW_HEIGHT }
    }
    const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 4)
    const visibleCount = Math.ceil(VIRTUAL_HEIGHT / ROW_HEIGHT) + 8
    const end = Math.min(rows.length, start + visibleCount)
    return {
      visibleRows: rows.slice(start, end),
      topSpace: start * ROW_HEIGHT,
      totalHeight: rows.length * ROW_HEIGHT,
    }
  }, [rows, scrollTop, useVirtual])

  if (useVirtual) {
    return (
      <div className="overflow-hidden rounded-2xl bg-surface-container">
        <HeaderRow />
        <div className="overflow-auto" style={{ height: VIRTUAL_HEIGHT }} onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}>
          <div style={{ height: virtualState.totalHeight, position: 'relative' }}>
            <div style={{ transform: `translateY(${virtualState.topSpace}px)` }}>
              {virtualState.visibleRows.map((row) => (
                <DataRow key={`${row.symbol}-${row.rank}`} row={row} onSelect={onSelect} />
              ))}
            </div>
          </div>
        </div>
        <div className="px-4 py-2.5 text-[11px] font-medium tracking-wider text-onSurface-variant">
          {formatNumber(rows.length)} rows
        </div>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl bg-surface-container">
      <HeaderRow />
      <div>
        {rows.map((row) => (
          <DataRow key={`${row.symbol}-${row.rank}`} row={row} onSelect={onSelect} />
        ))}
      </div>
      <div className="px-4 py-2.5 text-[11px] font-medium tracking-wider text-onSurface-variant">
        {formatNumber(rows.length)} rows
      </div>
    </div>
  )
}
