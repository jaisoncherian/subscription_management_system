import { api } from './client'

export const invoicesApi = {
  list: (params) => api('/invoices', { params }),
  get: (id) => api(`/invoices/${id}`),
  act: (id, action) => api(`/invoices/${id}/${action}`, { method: 'POST' }),
  payments: (id) => api(`/invoices/${id}/payments`),
  pay: (id, body) => api(`/invoices/${id}/payments`, { method: 'POST', body }),
  printUrl: (id) => `/api/invoices/${id}/print`,
}

export const paymentsApi = {
  list: (params) => api('/payments', { params }),
}

export const billingApi = {
  run: () => api('/billing/run', { method: 'POST' }),
}
