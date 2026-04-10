import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchCompanyBundle,
  fetchCompanyNews,
  fetchLivePrediction,
  fetchRecommendation,
  fetchRanking,
  fetchRankingHistory,
  triggerRefresh,
} from '../lib/api'

const refreshInterval = Number(import.meta.env.VITE_REFRESH_INTERVAL || 60_000)

export function useRankingQuery(options = {}) {
  return useQuery({
    queryKey: ['ranking'],
    queryFn: fetchRanking,
    refetchInterval: refreshInterval,
    ...options,
  })
}

export function useCompanyQuery(symbol) {
  return useQuery({
    queryKey: ['company', symbol],
    queryFn: () => fetchCompanyBundle(symbol),
    enabled: Boolean(symbol),
  })
}

export function useHistoryQuery(symbol) {
  return useQuery({
    queryKey: ['history', symbol],
    queryFn: () => fetchRankingHistory(symbol),
    enabled: Boolean(symbol),
  })
}

export function usePredictionQuery(symbol) {
  return useQuery({
    queryKey: ['prediction', symbol],
    queryFn: () => fetchLivePrediction(symbol),
    enabled: Boolean(symbol),
    staleTime: 30_000,
    retry: 1,
  })
}

export function useNewsQuery(symbol) {
  return useQuery({
    queryKey: ['news', symbol],
    queryFn: () => fetchCompanyNews(symbol),
    enabled: Boolean(symbol),
    staleTime: 45_000,
    retry: 1,
  })
}

export function useRecommendationQuery(symbol) {
  return useQuery({
    queryKey: ['recommendation', symbol],
    queryFn: () => fetchRecommendation(symbol),
    enabled: Boolean(symbol),
    staleTime: 45_000,
    retry: 1,
  })
}

export function useRefreshMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: triggerRefresh,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['ranking'] })
      const previous = queryClient.getQueryData(['ranking'])
      queryClient.setQueryData(['ranking'], (old) => old ?? previous ?? [])
      return { previous }
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['ranking'], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['ranking'] })
    },
  })
}
