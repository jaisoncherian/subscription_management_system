import { api } from './client'

export const templatesApi = {
  list: (params) => api('/quotation-templates', { params }),
  get: (id) => api(`/quotation-templates/${id}`),
  create: (body) => api('/quotation-templates', { method: 'POST', body }),
  update: (id, body) => api(`/quotation-templates/${id}`, { method: 'PUT', body }),
  deactivate: (id) => api(`/quotation-templates/${id}`, { method: 'DELETE' }),
}