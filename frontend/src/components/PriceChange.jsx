export default function PriceChange({ value }) {
  const safeValue = Number(value || 0)
  const isPositive = safeValue >= 0

  return (
    <span className={`text-sm font-medium ${isPositive ? 'text-positive' : 'text-negative'}`}>
      {isPositive ? '+' : ''}{safeValue.toFixed(2)}%
    </span>
  )
}
