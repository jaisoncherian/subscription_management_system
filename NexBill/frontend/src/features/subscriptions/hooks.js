import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { subscriptionsApi } from '../../api/subscriptions'

export const useSubscriptions = (params) =>
  useQuery({ queryKey: ['subscriptions', params], queryFn: () => subscriptionsApi.list(params), placeholderData: keepPreviousData })

export const useSubscription = (id) =>
  useQuery({ queryKey: ['subscription', id], queryFn: () => subscriptionsApi.get(id) })

export function useCreateSubscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: subscriptionsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['subscriptions'] }),
  })
}

export function useSubscriptionAction(id) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (action) => subscriptionsApi.act(id, action),
    onSuccess: (data) => {
      qc.setQueryData(['subscription', id], data)
      qc.invalidateQueries({ queryKey: ['subscriptions'] })
      qc.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: () => qc.invalidateQueries({ queryKey: ['subscription', id] }),
  })
}