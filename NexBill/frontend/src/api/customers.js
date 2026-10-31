import { api } from './client'

export const customersApi = {
  list: (params) => api('/customers', { params }),
  get: (id) => api(`/customers/${id}`),
  create: (body) => api('/customers', { method: 'POST', body }),
}