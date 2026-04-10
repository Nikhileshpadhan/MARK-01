export default function SkeletonTable() {
  return (
    <div className="rounded-2xl bg-surface-container p-6">
      <div className="mb-4 h-4 w-32 rounded bg-surface-container-high skeleton" />
      {Array.from({ length: 8 }).map((_, index) => (
        <div key={index} className="mb-3 h-10 rounded-lg bg-surface-container-high skeleton" style={{ opacity: 1 - index * 0.08 }} />
      ))}
    </div>
  )
}
