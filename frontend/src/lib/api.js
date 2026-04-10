import axios from 'axios'

const configuredBaseUrl = import.meta.env.VITE_API_URL
const defaultBaseUrl = 'http://127.0.0.1:8000'
const apiBaseUrl = configuredBaseUrl || defaultBaseUrl

function alternateBaseUrl(baseUrl) {
  if (baseUrl.includes('localhost')) {
    return baseUrl.replace('localhost', '127.0.0.1')
  }
  if (baseUrl.includes('127.0.0.1')) {
    return baseUrl.replace('127.0.0.1', 'localhost')
  }
  return null
}

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15_000,
})

async function getWithFallback(path) {
  try {
    const response = await apiClient.get(path)
    return response.data
  } catch (error) {
    const fallbackBaseUrl = alternateBaseUrl(apiBaseUrl)
    if (!fallbackBaseUrl) {
      throw error
    }
    const fallbackClient = axios.create({ baseURL: fallbackBaseUrl, timeout: 15_000 })
    const response = await fallbackClient.get(path)
    return response.data
  }
}

export async function fetchRanking() {
  const data = await getWithFallback('/ranking/latest')
  return Array.isArray(data) ? data : []
}

export async function fetchRankingHistory(symbol) {
  const data = await getWithFallback(`/ranking/history/${symbol}`)
  return data
}

export async function fetchCompanyBundle(symbol) {
  const [stockLatest, stockHistory, engagementLatest, engagementHistory, rankingHistory] = await Promise.all([
    apiClient.get(`/stock/${symbol}/latest`),
    apiClient.get(`/stock/${symbol}/market-history?days=30`).catch(() => apiClient.get(`/stock/${symbol}/history?limit=30`)),
    apiClient.get(`/engagement/${symbol}/latest`),
    apiClient.get(`/engagement/${symbol}/history?limit=30`),
    apiClient.get(`/ranking/history/${symbol}`),
  ])

  return {
    stockLatest: stockLatest.data,
    stockHistory: stockHistory.data,
    engagementLatest: engagementLatest.data,
    engagementHistory: engagementHistory.data,
    rankingHistory: rankingHistory.data,
  }
}

export async function fetchLivePrediction(symbol) {
  const data = await getWithFallback(`/prediction/${symbol}/live`)
  return data
}

export async function fetchCompanyNews(symbol, limit = 8) {
  const data = await getWithFallback(`/news/${symbol}?limit=${limit}`)
  return data
}

export async function fetchRecommendation(symbol) {
  const data = await getWithFallback(`/recommendation/${symbol}/live`)
  return data
}

export async function triggerRefresh() {
  const { data } = await apiClient.post('/refresh')
  return data
}

export async function searchCompanies(query) {
  if (!query || query.trim().length === 0) return []
  const data = await getWithFallback(`/companies/search?q=${encodeURIComponent(query.trim())}`)
  return Array.isArray(data) ? data : []
}
