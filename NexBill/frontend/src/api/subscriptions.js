import { api } from './client'

export const subscriptionsApi = {
  list: (params) => api('/subscriptions', { params }),
  get: (id) => api(`/subscriptions/${id}`),
  create: (body) => api('/subscriptions', { method: 'POST', body }),
  act: (id, action) => api(`/subscriptions/${id}/${action}`, { method: 'POST' }),
}