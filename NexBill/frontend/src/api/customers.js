import { api } from './client'

export const customersApi = {
  list: (params) => api('/customers', { params }),
}