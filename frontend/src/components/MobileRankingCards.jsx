import EngagementBadge from './EngagementBadge'
import PriceChange from './PriceChange'
import { formatPrice } from '../utils/format'

export default function MobileRankingCards({ rows, onSelect }) {
  return (
    <div className="space-y-2 md:hidden">
      {rows.map((row) => (
        <button
          key={`${row.symbol}-${row.rank}`}
          type="button"
          onClick={() => onSelect(row.symbol)}
          className="w-full rounded-xl bg-surface-container p-4 text-left transition-colors duration-200 hover:bg-surface-container-high"
        >
          <div className="mb-3 flex items-center justify-between">
            <div>
              <p className="text-base font-semibold text-onSurface">{row.symbol}</p>
              <p className="text-xs text-onSurface-variant">{row.name}</p>
            </div>
            <span className="rounded-full bg-surface-container-high px-2.5 py-0.5 text-xs font-medium text-positive">
              #{row.rank}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-onSurface-variant">Price</p>
              <p className="mt-0.5 font-medium tabular-nums text-onSurface">{formatPrice(row.price)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-onSurface-variant">Change</p>
              <div className="mt-0.5"><PriceChange value={row.change_percent} /></div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-onSurface-variant">Engagement</p>
              <div className="mt-0.5"><EngagementBadge count={row.mention_count} /></div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-onSurface-variant">Score</p>
              <p className="mt-0.5 font-semibold tabular-nums text-positive">{Number(row.final_score ?? 0).toFixed(1)}</p>
            </div>
          </div>
        </button>
      ))}
    </div>
  )
}
