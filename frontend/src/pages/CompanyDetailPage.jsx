import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AnimatedNumber from '../components/AnimatedNumber'
import PriceChange from '../components/PriceChange'
import SkeletonTable from '../components/SkeletonTable'
import { useCompanyQuery, useHistoryQuery, useNewsQuery, usePredictionQuery, useRecommendationQuery } from '../hooks/useDashboardData'
import { formatNumber, formatPrice, toShortDate } from '../utils/format'

function toSafeNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function formatChartDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const chartTooltipStyle = {
  background: '#201F1F',
  border: '1px solid #2A2A2A',
  borderRadius: '12px',
  color: '#E5E2E1',
  fontSize: '12px',
  padding: '8px 12px',
}

function SentimentBadge({ score }) {
  if (score === null || score === undefined) {
    return <span className="rounded-full bg-surface-container-high px-3 py-1 text-xs font-medium text-onSurface-variant">Unknown</span>
  }
  if (score >= 0.66) {
    return <span className="rounded-full bg-positive/15 px-3 py-1 text-xs font-medium text-positive">Positive</span>
  }
  if (score >= 0.4) {
    return <span className="rounded-full bg-primary-container/15 px-3 py-1 text-xs font-medium text-primary">Neutral</span>
  }
  return <span className="rounded-full bg-negative/15 px-3 py-1 text-xs font-medium text-negative">Negative</span>
}

function MetricCard({ label, children }) {
  return (
    <div className="dashboard-card-hover rounded-2xl bg-surface-container-lowest p-5 h-full">
      <p className="text-[11px] font-medium uppercase tracking-widest text-onSurface-variant/70">{label}</p>
      <div className="mt-2.5">{children}</div>
    </div>
  )
}

function SectionCard({ title, subtitle, badge, children }) {
  return (
    <div className="dashboard-card-hover rounded-2xl bg-surface-container p-6">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-xs font-medium uppercase tracking-widest text-onSurface-variant/70">{title}</h3>
          {subtitle && <p className="mt-1 text-xs text-onSurface-variant/70">{subtitle}</p>}
        </div>
        {badge && <span className="shrink-0 text-xs text-onSurface-variant/70">{badge}</span>}
      </div>
      {children}
    </div>
  )
}

export default function CompanyDetailPage() {
  const navigate = useNavigate()
  const { symbol = '' } = useParams()
  const companyQuery = useCompanyQuery(symbol)
  const historyQuery = useHistoryQuery(symbol)
  const predictionQuery = usePredictionQuery(symbol)
  const newsQuery = useNewsQuery(symbol)
  const recommendationQuery = useRecommendationQuery(symbol)

  const detail = companyQuery.data
  const rankingHistory = historyQuery.data || detail?.rankingHistory || []

  const stockSeries = (() => {
    const items = Array.isArray(detail?.stockHistory) ? [...detail.stockHistory] : []
    return items
      .filter((item) => item && item.timestamp)
      .sort((left, right) => new Date(left.timestamp) - new Date(right.timestamp))
      .filter((item, index, array) => index === 0 || item.timestamp !== array[index - 1].timestamp)
      .map((item) => ({
        timestamp: item.timestamp,
        dayLabel: toShortDate(item.timestamp),
        price: toSafeNumber(item.price),
        volume: Math.max(0, toSafeNumber(item.volume)),
        isStale: Boolean(item.is_stale),
      }))
  })()

  const sparklineData = stockSeries.slice(-7)
  const barData = stockSeries.slice(-30)

  const engagementScore = rankingHistory.length ? toSafeNumber(rankingHistory[0].engagement_score) : 0
  const priceScore = rankingHistory.length ? toSafeNumber(rankingHistory[0].price_score) : 0
  const finalScore = rankingHistory.length ? toSafeNumber(rankingHistory[0].final_score) : 0
  const sentimentScore = Math.max(0, Math.min(1, toSafeNumber(detail?.engagementLatest?.sentiment_score, 0)))
  const latestRank = rankingHistory.length ? rankingHistory[0].rank : null
  const progressStyle = {
    background: `conic-gradient(#00D09C ${Math.max(0, Math.min(100, engagementScore))}%, rgba(255,255,255,0.06) 0%)`,
  }

  const newsItems = newsQuery.data?.items?.slice(0, 4) || []
  const latestStockPoint = sparklineData.length ? sparklineData[sparklineData.length - 1] : null
  const hasVolumeData = barData.some((item) => item.volume > 0)
  const sevenDayTrend = useMemo(() => {
    if (sparklineData.length < 2) {
      return null
    }

    const startPoint = sparklineData[0]
    const endPoint = sparklineData[sparklineData.length - 1]
    const netChange = toSafeNumber(endPoint.price) - toSafeNumber(startPoint.price)
    const percentChange = toSafeNumber(startPoint.price) === 0
      ? null
      : (netChange / toSafeNumber(startPoint.price)) * 100

    return {
      startPrice: toSafeNumber(startPoint.price),
      endPrice: toSafeNumber(endPoint.price),
      netChange,
      percentChange,
    }
  }, [sparklineData])

  if (companyQuery.isLoading || historyQuery.isLoading) {
    return <SkeletonTable />
  }

  if (companyQuery.isError) {
    return (
      <div className="rounded-2xl bg-surface-container p-6 text-negative">
        Unable to load details for {symbol}.
      </div>
    )
  }

  if (historyQuery.isError) {
    return (
      <div className="rounded-2xl bg-surface-container p-6 text-negative">
        Unable to load ranking history for {symbol}. Please refresh and try again.
      </div>
    )
  }

  return (
    <section className="space-y-8 pb-10">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="rounded-full bg-surface-container px-4 py-2 text-sm font-medium text-onSurface-variant transition-colors duration-200 hover:bg-surface-container-high hover:text-onSurface"
      >
        ← Back to ranking
      </button>

      <div className="grid gap-6 xl:grid-cols-[1.95fr_1.05fr_1fr]">
        <div className="space-y-6 xl:col-span-2">
          <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
            <div className="fade-up-card dashboard-card-hover overflow-hidden rounded-3xl bg-gradient-to-br from-surface-container via-surface-container-low to-surface-container-lowest p-6" style={{ '--enter-delay': '0ms' }}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-[0.25em] text-onSurface-variant/70">Company overview</p>
                  <h2 className="mt-2 text-4xl font-semibold tracking-tight text-onSurface md:text-5xl">{symbol}</h2>
                  <p className="mt-1 text-sm text-onSurface-variant/70">Real-time market, engagement, and prediction dashboard</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-surface-container-high px-3 py-1 text-xs font-medium text-onSurface-variant/70">
                    Rank #{latestRank || 'N/A'}
                  </span>
                  <span className="rounded-full bg-surface-container-high px-3 py-1 text-xs font-medium text-onSurface-variant/70">
                    {detail?.sector || 'Sector N/A'}
                  </span>
                  <span className="live-badge-pulse rounded-full bg-positive/10 px-3 py-1 text-xs font-medium text-positive">
                    Live data
                  </span>
                </div>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Price">
                  <p className="text-2xl font-semibold tabular-nums tracking-tight text-onSurface">
                    <AnimatedNumber value={detail?.stockLatest?.price} formatter={(num) => formatPrice(num)} />
                  </p>
                  <div className="mt-1.5"><PriceChange value={detail?.stockLatest?.change_percent} /></div>
                  {latestStockPoint && (
                    <p className="mt-2 text-[10px] text-onSurface-variant/70">{formatChartDateTime(latestStockPoint.timestamp)}</p>
                  )}
                </MetricCard>

                <MetricCard label="Volume">
                  <p className="text-2xl font-semibold tabular-nums tracking-tight text-onSurface">{formatNumber(detail?.stockLatest?.volume)}</p>
                  <p className="mt-1.5 text-xs text-onSurface-variant/70">Latest session</p>
                </MetricCard>

                <MetricCard label="Composite Score">
                  <p className="text-2xl font-semibold tabular-nums tracking-tight text-positive">{finalScore.toFixed(1)}</p>
                  <p className="mt-1.5 text-xs text-onSurface-variant/70">Ranking blend</p>
                </MetricCard>

                <MetricCard label="Sentiment">
                  <div className="mt-1"><SentimentBadge score={detail?.engagementLatest?.sentiment_score} /></div>
                  <p className="mt-2.5 text-xs text-onSurface-variant/70">Current engagement view</p>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-container-high">
                    <div
                      className="sentiment-progress h-full w-full rounded-full bg-primary-container"
                      style={{ transform: `scaleX(${sentimentScore})`, transformOrigin: 'left center' }}
                    />
                  </div>
                </MetricCard>
              </div>
            </div>

            <SectionCard title="Engagement snapshot" subtitle="Score and recent activity" badge="Real-time">
              <div className="fade-up-card flex h-full flex-col justify-center" style={{ '--enter-delay': '50ms' }}>
                <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full" style={progressStyle}>
                  <div className="flex h-24 w-24 items-center justify-center rounded-full bg-surface-container text-2xl font-semibold tabular-nums text-primary-container">
                    {engagementScore.toFixed(0)}
                  </div>
                </div>
                <div className="mt-6 grid grid-cols-2 gap-3">
                  <div className="dashboard-card-hover rounded-xl bg-surface-container-lowest px-3.5 py-3">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Price score</p>
                    <p className="mt-1 text-base font-semibold tabular-nums text-positive">{priceScore.toFixed(1)}</p>
                  </div>
                  <div className="dashboard-card-hover rounded-xl bg-surface-container-lowest px-3.5 py-3">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Engagement</p>
                    <p className="mt-1 text-base font-semibold tabular-nums text-primary-container">{engagementScore.toFixed(1)}</p>
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.85fr_1fr]">
            <div className="space-y-6">
              <SectionCard
                title="Live stock trend"
                subtitle="Last 7 trading days (start vs latest)"
                badge={sevenDayTrend ? '7-day delta' : '7-day line'}
              >
                <div className="fade-up-card chart-fade-in min-h-[420px]" style={{ '--enter-delay': '100ms' }}>
              {sevenDayTrend && (
                <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <div className="rounded-lg bg-surface-container-lowest px-3 py-2">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">7d start</p>
                    <p className="mt-1 text-sm font-semibold tabular-nums text-onSurface">{formatPrice(sevenDayTrend.startPrice)}</p>
                  </div>
                  <div className="rounded-lg bg-surface-container-lowest px-3 py-2">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Latest</p>
                    <p className="mt-1 text-sm font-semibold tabular-nums text-onSurface">{formatPrice(sevenDayTrend.endPrice)}</p>
                  </div>
                  <div className="rounded-lg bg-surface-container-lowest px-3 py-2">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Net 7d change</p>
                    <p className={`mt-1 text-sm font-semibold tabular-nums ${sevenDayTrend.netChange >= 0 ? 'text-positive' : 'text-negative'}`}>
                      {sevenDayTrend.netChange >= 0 ? '+' : ''}{formatPrice(sevenDayTrend.netChange)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-surface-container-lowest px-3 py-2">
                    <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Net 7d %</p>
                    <p className={`mt-1 text-sm font-semibold tabular-nums ${(sevenDayTrend.percentChange || 0) >= 0 ? 'text-positive' : 'text-negative'}`}>
                      {sevenDayTrend.percentChange === null
                        ? 'N/A'
                        : `${sevenDayTrend.percentChange >= 0 ? '+' : ''}${sevenDayTrend.percentChange.toFixed(2)}%`}
                    </p>
                  </div>
                </div>
              )}
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sparklineData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="#2A2A2A" strokeDasharray="3 3" />
                    <XAxis dataKey="dayLabel" minTickGap={18} tick={{ fill: '#C0C7D4', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#C0C7D4', fontSize: 11 }} width={42} />
                    <Tooltip
                      labelFormatter={(_, payload) => formatChartDateTime(payload?.[0]?.payload?.timestamp)}
                      formatter={(value) => [formatPrice(value), 'Price']}
                      contentStyle={chartTooltipStyle}
                    />
                    <Line type="monotone" dataKey="price" stroke="#00D09C" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
                </div>
              </SectionCard>

              <SectionCard title="Volume profile" subtitle="30-day daily volume" badge="Bar chart">
                <div className="fade-up-card chart-fade-in" style={{ '--enter-delay': '150ms' }}>
            {hasVolumeData ? (
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="#2A2A2A" strokeDasharray="3 3" />
                    <XAxis dataKey="dayLabel" minTickGap={18} tick={{ fill: '#C0C7D4', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#C0C7D4', fontSize: 11 }} width={46} />
                    <Tooltip
                      labelFormatter={(_, payload) => formatChartDateTime(payload?.[0]?.payload?.timestamp)}
                      contentStyle={chartTooltipStyle}
                    />
                    <Bar dataKey="volume" fill="#00D09C" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="rounded-xl bg-surface-container-lowest p-4 text-sm text-onSurface-variant">
                Volume data is not available in the recent snapshots.
              </div>
            )}
                </div>
              </SectionCard>
            </div>

            <div className="space-y-6">
              <SectionCard
                title="Price prediction"
                subtitle="Next-day forecast based on market data"
              >
                <div className="fade-up-card min-h-[420px]" style={{ '--enter-delay': '200ms' }}>
                {predictionQuery.isLoading ? (
                  <div className="space-y-2.5">
                    <div className="h-4 w-3/4 rounded bg-surface-container-high skeleton" />
                    <div className="h-4 w-1/2 rounded bg-surface-container-high skeleton" />
                  </div>
                ) : predictionQuery.isError ? (
                  <p className="text-sm text-negative">Prediction is temporarily unavailable.</p>
                ) : predictionQuery.data ? (
                  <div className="space-y-3">
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="dashboard-card-hover rounded-xl bg-surface-container-lowest p-4">
                        <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Predicted price</p>
                        <p className="mt-1.5 text-xl font-semibold tabular-nums text-onSurface">
                          <AnimatedNumber value={predictionQuery.data.predicted_price} formatter={(num) => formatPrice(num)} />
                        </p>
                      </div>
                      <div className="dashboard-card-hover rounded-xl bg-surface-container-lowest p-4">
                        <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Expected move</p>
                        <p className={`mt-1.5 text-xl font-semibold tabular-nums ${toSafeNumber(predictionQuery.data.predicted_change_percent) >= 0 ? 'text-positive' : 'text-negative'}`}>
                          <AnimatedNumber
                            value={toSafeNumber(predictionQuery.data.predicted_change_percent)}
                            formatter={(num) => `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`}
                          />
                        </p>
                      </div>
                    </div>
                    <div className="dashboard-card-hover rounded-lg bg-surface-container-lowest px-3.5 py-2.5">
                      <p className="text-[10px] font-medium uppercase tracking-widest text-onSurface-variant/70">Source</p>
                      <p className="mt-1 text-sm font-medium text-onSurface">Live market data</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-onSurface-variant">No prediction data available.</p>
                )}
                </div>
              </SectionCard>

              <SectionCard
                title="AI recommendation"
                subtitle="Groq-powered buy/sell/hold feedback"
              >
                <div className="fade-up-card" style={{ '--enter-delay': '250ms' }}>
                {recommendationQuery.isLoading ? (
                  <div className="space-y-2.5">
                    <div className="h-4 w-3/4 rounded bg-surface-container-high skeleton" />
                    <div className="h-4 w-1/2 rounded bg-surface-container-high skeleton" />
                  </div>
                ) : recommendationQuery.isError ? (
                  <p className="text-sm text-negative">Recommendation is temporarily unavailable.</p>
                ) : recommendationQuery.data ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${recommendationQuery.data.action === 'BUY' ? 'bg-positive/15 text-positive' : recommendationQuery.data.action === 'SELL' ? 'bg-negative/15 text-negative' : 'bg-primary-container/15 text-primary'}`}>
                        {recommendationQuery.data.action}
                      </span>
                      <span className="rounded-full bg-surface-container-lowest px-3 py-1 text-xs font-medium text-onSurface-variant/70">
                        Confidence: {recommendationQuery.data.confidence}
                      </span>
                    </div>
                    <p className="text-sm leading-6 text-onSurface-variant/70">{recommendationQuery.data.summary}</p>
                  </div>
                ) : (
                  <p className="text-sm text-onSurface-variant">No recommendation available.</p>
                )}
                </div>
              </SectionCard>
            </div>
          </div>
        </div>

        <div className="xl:sticky xl:top-28 xl:self-start">
          <SectionCard title="Live news" subtitle="Top company updates" badge={`${newsItems.length} items`}>
            <div className="fade-up-card" style={{ '--enter-delay': '300ms' }}>
            {newsQuery.isLoading ? (
              <div className="space-y-2.5">
                <div className="h-16 rounded-xl bg-surface-container-high skeleton" />
                <div className="h-16 rounded-xl bg-surface-container-high skeleton" />
                <div className="h-16 rounded-xl bg-surface-container-high skeleton" />
              </div>
            ) : newsQuery.isError ? (
              <p className="text-sm text-negative">News feed is temporarily unavailable.</p>
            ) : newsItems.length ? (
              <div className="news-scroll max-h-[640px] space-y-3 overflow-auto pr-1">
                {newsItems.map((item, index) => (
                  <a
                    key={`${item.url}-${index}`}
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="news-item block rounded-xl bg-surface-container-lowest p-4"
                  >
                    <div className="flex items-start justify-between gap-2.5">
                      <p className="text-sm font-medium leading-5 text-onSurface">{item.title}</p>
                      <span className="shrink-0 rounded-full bg-surface-container-high px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-onSurface-variant/70">
                        {item.source}
                      </span>
                    </div>
                    {item.summary && <p className="mt-2 text-xs leading-5 text-onSurface-variant/70 line-clamp-3">{item.summary}</p>}
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-sm text-onSurface-variant">No news available for this company.</p>
            )}
            </div>
          </SectionCard>
        </div>
      </div>

      <div className="rounded-2xl border border-negative/25 bg-surface-container p-4 text-xs text-onSurface-variant/80">
        Warning: This analysis can make mistakes. Use it at your own risk.
      </div>
    </section>
  )
}
