import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import AnimatedNumber from '../components/AnimatedNumber'

const marketTape = [
  { symbol: 'AAPL', change: '+1.15%' },
  { symbol: 'NVDA', change: '+2.44%' },
  { symbol: 'MSFT', change: '+0.74%' },
  { symbol: 'TSLA', change: '-0.92%' },
  { symbol: 'META', change: '+1.38%' },
  { symbol: 'AMZN', change: '+0.69%' },
]

const trustedBy = ['Apex Capital', 'NorthGrid Labs', 'Helios Funds', 'Crestline Analytics', 'Monarch Trading']

const stats = [
  { label: 'Coverage', value: 50, suffix: '+ Companies' },
  { label: 'Refresh Loop', value: 60, suffix: 's' },
  { label: 'Pipeline', value: 2, suffix: ' Core Layers' },
]

const features = [
  {
    title: 'Live Market Ranking',
    description: 'Track ranked equities in real time using normalized score intelligence from price and engagement signals.',
  },
  {
    title: 'Sentiment Intelligence',
    description: 'Spot momentum shifts with engagement streams blended into your stock scoring pipeline.',
  },
  {
    title: 'Analyst-Friendly Detail',
    description: 'Open instant detail views for trend charts, score decomposition, and historical change patterns.',
  },
]

const workflow = [
  'Aggregate stock snapshots from FinHub with fallback reliability.',
  'Collect and normalize engagement from high-signal communities.',
  'Generate transparent ranking scores on a continuous refresh cycle.',
  'Deliver insights through a fast, responsive dashboard interface.',
]

export default function LandingPage() {
  const timelineRef = useRef(null)
  const [isTimelineVisible, setIsTimelineVisible] = useState(false)

  useEffect(() => {
    const element = timelineRef.current
    if (!element) return () => {}

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsTimelineVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.25 },
    )

    observer.observe(element)

    return () => observer.disconnect()
  }, [])

  return (
    <section className="landing-shell relative space-y-8 overflow-hidden">
      <div className="landing-depth-overlay" aria-hidden="true" />
      <div className="landing-noise-overlay" aria-hidden="true" />

      {/* Hero */}
      <div className="landing-panel rounded-3xl p-8 md:p-12">
        <div className="grid gap-10 lg:grid-cols-12 lg:items-center">
          <div className="max-w-2xl lg:col-span-7">
            <p className="landing-reveal mb-4 inline-flex rounded-full bg-surface-container-high px-3.5 py-1 text-[11px] font-medium uppercase tracking-widest text-onSurface-variant/75" style={{ '--enter-delay': '0ms' }}>
              Enterprise-Grade Market Intelligence
            </p>
            <h2 className="landing-reveal text-3xl font-semibold leading-tight tracking-tight text-onSurface md:text-5xl md:leading-tight" style={{ '--enter-delay': '60ms' }}>
              The command center for ranked equities, sentiment momentum, and actionable signals.
            </h2>
            <p className="landing-reveal mt-5 max-w-xl text-sm leading-relaxed text-onSurface-variant/75 md:text-base" style={{ '--enter-delay': '120ms' }}>
              MarketMind combines market performance and public engagement into one transparent score,
              so teams can move from noise to conviction in seconds.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <NavLink
                to="/dashboard"
                className="landing-reveal landing-btn landing-btn-primary" style={{ '--enter-delay': '170ms' }}
              >
                Open Live Dashboard
              </NavLink>
              <a
                href="#platform-features"
                className="landing-reveal landing-btn landing-btn-secondary" style={{ '--enter-delay': '220ms' }}
              >
                View Platform
              </a>
            </div>
          </div>

          <div className="landing-snapshot-card landing-reveal lg:col-span-5" style={{ '--enter-delay': '180ms' }}>
            <p className="mb-3 text-[11px] font-medium uppercase tracking-widest text-onSurface-variant/75">Market Snapshot</p>
            <div className="grid grid-cols-2 gap-2.5">
              {marketTape.map((item) => {
                const signedValue = Number(item.change.replace('%', ''))
                const positive = signedValue >= 0
                return (
                  <div key={item.symbol} className="snapshot-chip rounded-xl bg-surface-container px-3.5 py-2.5">
                    <p className="text-xs text-onSurface-variant/75">{item.symbol}</p>
                    <p className={`mt-0.5 flex items-center gap-1.5 text-sm font-semibold tabular-nums ${positive ? 'text-positive' : 'text-negative/80'}`}>
                      <span className={`snapshot-dot ${positive ? 'bg-positive/80 shadow-[0_0_8px_rgba(0,208,156,0.45)]' : 'bg-negative/70'}`} />
                      <AnimatedNumber value={signedValue} formatter={(num) => `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`} />
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Trusted by */}
      <div className="landing-panel rounded-2xl p-5">
        <div className="mb-4 border-t border-white/10 pt-4">
          <p className="text-[11px] font-medium uppercase tracking-widest text-onSurface-variant/75">Trusted by teams at</p>
        </div>
        <div className="trusted-marquee">
          <div className="trusted-track">
            {[...trustedBy, ...trustedBy].map((name, index) => (
              <div key={`${name}-${index}`} className="trusted-chip rounded-lg bg-surface-container px-4 py-2.5 text-center text-sm text-onSurface-variant/80">
                {name}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        {stats.map((stat, index) => (
          <div key={stat.label} className="landing-stat-card rounded-2xl p-6">
            <p className="text-[11px] font-medium uppercase tracking-widest text-onSurface-variant/75">{stat.label}</p>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-onSurface">
              <AnimatedNumber
                value={stat.value}
                formatter={(num) => `${Math.round(num)}${stat.suffix}`}
                duration={600 + index * 80}
              />
            </p>
          </div>
        ))}
      </div>

      {/* Features */}
      <div id="platform-features" className="landing-panel rounded-3xl p-6 md:p-8">
        <div className="mb-6 flex items-center justify-between gap-2">
          <h3 className="text-xl font-semibold text-onSurface">Platform Features</h3>
          <span className="rounded-full bg-surface-container-high px-3.5 py-1 text-[11px] font-medium text-onSurface-variant/75">
            Built for speed
          </span>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {features.map((feature, index) => (
            <article key={feature.title} className="feature-card rounded-xl bg-surface-container-low p-5" style={{ '--enter-delay': `${index * 60}ms` }}>
              <div className="mb-3 flex items-center gap-2">
                <span className="feature-icon" aria-hidden="true" />
                <h4 className="text-base font-semibold text-onSurface">{feature.title}</h4>
              </div>
              <p className="text-sm leading-relaxed text-onSurface-variant/75">{feature.description}</p>
            </article>
          ))}
        </div>
      </div>

      {/* How it works */}
      <div ref={timelineRef} className="landing-panel rounded-3xl p-6 md:p-8">
        <h3 className="text-xl font-semibold text-onSurface">How It Works</h3>
        <ol className="timeline-list mt-6">
          <div className={`timeline-progress ${isTimelineVisible ? 'is-visible' : ''}`} aria-hidden="true" />
          {workflow.map((step, index) => (
            <li key={step} className={`timeline-step ${isTimelineVisible ? 'is-visible' : ''}`} style={{ '--step-delay': `${index * 80}ms` }}>
              <span className="timeline-node" aria-hidden="true">{index + 1}</span>
              <div className="rounded-xl bg-surface-container-low px-5 py-3.5 text-sm text-onSurface-variant/75">
                {step}
              </div>
            </li>
          ))}
        </ol>
      </div>

      {/* CTA */}
      <div className="landing-panel rounded-3xl bg-gradient-to-r from-primary-container/15 via-surface-container to-surface p-6 md:p-8">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <h3 className="text-2xl font-semibold tracking-tight text-onSurface">
              Ready to monitor market movers?
            </h3>
            <p className="mt-2 text-sm text-onSurface-variant/75">
              Launch the dashboard and start tracking high-signal opportunities in real time.
            </p>
          </div>
          <NavLink
            to="/dashboard"
            className="landing-btn landing-btn-primary"
          >
            Go to Dashboard
          </NavLink>
        </div>
      </div>
    </section>
  )
}
