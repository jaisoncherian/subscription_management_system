import { useQuery } from '@tanstack/react-query'
import { customersApi } from '../../api/customers'

export const useCustomers = (params) =>
  useQuery({ queryKey: ['customers', params], queryFn: () => customersApi.list(params) })