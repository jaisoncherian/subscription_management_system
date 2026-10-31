import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import Modal from '../../components/Modal'
import Button from '../../components/Button'
import { FormField, Input, Select, Textarea } from '../../components/FormField'
import { useToast } from '../../components/Toast'
import { subscriptionSchema } from '../../schemas/subscription'
import { applyServerError } from '../../utils/formErrors'
import { useCustomers } from '../customers/hooks'
import { useTemplates } from '../templates/hooks'
import { useCreateSubscription } from './hooks'

export default function SubscriptionCreateModal({ open, onClose }) {
  const navigate = useNavigate()
  const toast = useToast()
  const customers = useCustomers({ per_page: 100 })
  const templates = useTemplates({ per_page: 100 })
  const create = useCreateSubscription()
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(subscriptionSchema) })

  const close = () => { reset(); onClose() }

  const onSubmit = async (values) => {
    const body = Object.fromEntries(Object.entries(values).filter(([, v]) => v !== '' && v != null))
    try {
      const sub = await create.mutateAsync(body)
      toast.success(`Subscription ${sub.number ?? ''} created as draft`)
      close()
      navigate(`/subscriptions/${sub.id}`)
    } catch (err) {
      applyServerError(err, setError, toast)
    }
  }

  return (
    <Modal open={open} onClose={close} title="New subscription"
      footer={<>
        <Button variant="secondary" onClick={close}>Cancel</Button>
        <Button type="submit" form="subscription-form" loading={isSubmitting}>Create draft</Button>
      </>}>
      <form id="subscription-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="Customer" htmlFor="customer_id" error={errors.customer_id?.message}>
          <Select id="customer_id" invalid={errors.customer_id} defaultValue="" {...register('customer_id')}>
            <option value="" disabled>{customers.isLoading ? 'Loading…' : 'Select a customer'}</option>
            {customers.data?.items.map((c) => <option key={c.id} value={c.id}>{c.full_name} ({c.email})</option>)}
          </Select>
        </FormField>
        <FormField label="Quotation template" htmlFor="template_id" error={errors.template_id?.message}>
          <Select id="template_id" invalid={errors.template_id} defaultValue="" {...register('template_id')}>
            <option value="" disabled>{templates.isLoading ? 'Loading…' : 'Select a template'}</option>
            {templates.data?.items.map((t) => <option key={t.id} value={t.id}>{t.name}{t.plan ? ` · ${t.plan.name}` : ''}</option>)}
          </Select>
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Start date" htmlFor="start_date" error={errors.start_date?.message} hint="Optional">
            <Input id="start_date" type="date" invalid={errors.start_date} {...register('start_date')} />
          </FormField>
          <FormField label="Expires on" htmlFor="expires_on" error={errors.expires_on?.message} hint="Optional">
            <Input id="expires_on" type="date" invalid={errors.expires_on} {...register('expires_on')} />
          </FormField>
        </div>
        <FormField label="Notes (visible to the customer)" htmlFor="notes" error={errors.notes?.message} hint="Do not write internal comments here.">
          <Textarea id="notes" invalid={errors.notes} {...register('notes')} />
        </FormField>
      </form>
    </Modal>
  )
}