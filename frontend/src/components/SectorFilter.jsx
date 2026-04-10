export default function SectorFilter({ sectors, activeSector, onSelect }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {sectors.map((sector) => {
        const active = sector === activeSector
        return (
          <button
            key={sector}
            type="button"
            onClick={() => onSelect(sector)}
            className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-colors duration-200 ${
              active
                ? 'bg-primary-container text-white'
                : 'bg-surface-container text-onSurface-variant hover:bg-surface-container-high hover:text-onSurface'
            }`}
          >
            {sector}
          </button>
        )
      })}
    </div>
  )
}
