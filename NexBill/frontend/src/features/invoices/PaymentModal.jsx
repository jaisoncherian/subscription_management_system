import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Button from '../../components/Button'
import { FormField, Input, Select, Textarea } from '../../components/FormField'
import Modal from '../../components/Modal'
import { useToast } from '../../components/Toast'
import { invoicesApi } from '../../api/invoices'
import { todayISO } from '../../utils/format'
import { applyServerError } from '../../utils/formErrors'
import { PAYMENT_METHODS } from './paymentMethods'

export default function PaymentModal({ invoice, onClose }) {
  const toast = useToast()
  const qc = useQueryClient()
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({
    defaultValues: { method: 'card', amount: invoice.balance_due, payment_date: todayISO(), note: '' },
  })
  const pay = useMutation({
    mutationFn: (body) => invoicesApi.pay(invoice.id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoice', invoice.id] })
      qc.invalidateQueries({ queryKey: ['invoice-payments', invoice.id] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['payments'] })
      qc.invalidateQueries({ queryKey: ['reports'] })
    },
  })

  const onSubmit = async ({ note, ...values }) => {
    try {
      await pay.mutateAsync(note ? { ...values, note } : values)
      toast.success('Payment recorded')
      onClose()
    } catch (err) {
      applyServerError(err, setError, toast)
    }
  }

  return (
    <Modal open onClose={onClose} title={`Record payment on ${invoice.invoice_number}`}
      footer={<>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button type="submit" form="payment-form" loading={isSubmitting}>Record payment</Button>
      </>}>
      <form id="payment-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="Method" htmlFor="method" error={errors.method?.message}>
          <Select id="method" invalid={errors.method} {...register('method')}>
            {PAYMENT_METHODS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </Select>
        </FormField>
        <FormField label="Amount" htmlFor="amount" error={errors.amount?.message} hint={`Balance due: ${invoice.balance_due}`}>
          <Input id="amount" inputMode="decimal" invalid={errors.amount} {...register('amount')} />
        </FormField>
        <FormField label="Payment date" htmlFor="payment_date" error={errors.payment_date?.message}>
          <Input id="payment_date" type="date" invalid={errors.payment_date} {...register('payment_date')} />
        </FormField>
        <FormField label="Note" htmlFor="note" error={errors.note?.message} hint="Optional">
          <Textarea id="note" invalid={errors.note} {...register('note')} />
        </FormField>
      </form>
    </Modal>
  )
}
