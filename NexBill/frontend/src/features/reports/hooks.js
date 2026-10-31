import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { reportsApi } from '../../api/reports'

export const useSummary = (params) => useQuery({ queryKey: ['reports', 'summary', params], queryFn: () => reportsApi.summary(params) })
export const useRevenue = (params) => useQuery({ queryKey: ['reports', 'revenue', params], queryFn: () => reportsApi.revenue(params) })
export const useOverdue = (params) =>
  useQuery({ queryKey: ['reports', 'overdue', params], queryFn: () => reportsApi.overdue(params), placeholderData: keepPreviousData })