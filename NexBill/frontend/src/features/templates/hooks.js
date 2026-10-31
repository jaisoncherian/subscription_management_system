import { useQuery } from '@tanstack/react-query'
import { templatesApi } from '../../api/templates'

export const useTemplates = (params) =>
  useQuery({ queryKey: ['templates', params], queryFn: () => templatesApi.list(params) })