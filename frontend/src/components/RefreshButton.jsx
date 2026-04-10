export default function RefreshButton({ onClick, isLoading }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isLoading}
      className="inline-flex items-center gap-2 rounded-full bg-surface-container-high px-4 py-2 text-sm font-medium text-onSurface transition-colors duration-200 hover:bg-surface-bright disabled:opacity-50"
    >
      <svg
        className={`h-4 w-4 ${isLoading ? 'animate-refresh-turn' : ''}`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
        <path d="M16 21h5v-5" />
      </svg>
      Refresh
    </button>
  )
}
