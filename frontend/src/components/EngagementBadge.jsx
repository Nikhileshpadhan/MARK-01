export default function EngagementBadge({ count }) {
  const safe = Number(count || 0)

  if (safe > 1000) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-engagement/15 px-2.5 py-0.5 text-xs font-medium text-primary-container">
        <span className="h-1.5 w-1.5 rounded-full bg-primary-container" />
        High
      </span>
    )
  }
  if (safe >= 100) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-positive/10 px-2.5 py-0.5 text-xs font-medium text-positive">
        <span className="h-1.5 w-1.5 rounded-full bg-positive" />
        Active
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-container-high px-2.5 py-0.5 text-xs font-medium text-onSurface-variant">
      <span className="h-1.5 w-1.5 rounded-full bg-onSurface-variant" />
      Low
    </span>
  )
}
