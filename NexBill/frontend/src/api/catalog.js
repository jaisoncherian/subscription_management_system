import { api } from './client'

const resource = (path) => ({
  list: (params) => api(path, { params }),
  create: (body) => api(path, { method: 'POST', body }),
  deactivate: (id) => api(`${path}/${id}`, { method: 'DELETE' }),
})

export const taxesApi = resource('/taxes')
export const productsApi = resource('/products')
export const plansApi = resource('/plans')
export const discountsApi = resource('/discounts')
export const staffApi = {
  list: (params) => api('/staff', { params }),
  create: (body) => api('/staff', { method: 'POST', body }),
}
