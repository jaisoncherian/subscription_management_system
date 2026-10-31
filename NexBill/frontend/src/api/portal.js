import { api } from './client'

export const portalApi = {
  subscriptions: (params) => api('/portal/subscriptions', { params }),
  invoices: (params) => api('/portal/invoices', { params }),
}
