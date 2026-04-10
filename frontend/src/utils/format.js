export function formatPrice(value) {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatNumber(value) {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  return new Intl.NumberFormat('en-US').format(value)
}

export function formatTimestamp(value) {
  if (!value) {
    return 'N/A'
  }
  return new Date(value).toLocaleDateString()
}

export function toShortDate(value) {
  if (!value) {
    return ''
  }
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
