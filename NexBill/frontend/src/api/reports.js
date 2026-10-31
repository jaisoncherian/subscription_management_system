import { api } from './client'

export const reportsApi = {
  summary: (params) => api('/reports/summary', { params }),
  revenue: (params) => api('/reports/revenue', { params: { group: 'month', ...params } }),
  overdue: (params) => api('/reports/overdue', { params }),
}