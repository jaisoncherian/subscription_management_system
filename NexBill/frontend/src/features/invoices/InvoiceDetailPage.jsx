import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import Button from '../../components/Button'
import ConfirmDialog from '../../components/ConfirmDialog'
import DataTable from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import PageHeader from '../../components/PageHeader'
import Spinner from '../../components/Spinner'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../components/Toast'
import { invoicesApi } from '../../api/invoices'
import { formatDate, formatMoney } from '../../utils/format'
import { useAuth } from '../auth/AuthContext'
import PaymentModal from './PaymentModal'
import { paymentMethodLabel } from './paymentMethods'

// How to display each action. Which ones apply comes from the API's allowed_actions.
const ACTIONS = {
  confirm: { label: 'Confirm', variant: 'primary' },
  send: { label: 'Send to customer', variant: 'secondary' },
  cancel: {
    label: 'Cancel invoice',
    variant: 'danger',
    confirm: { title: 'Cancel this invoice?', message: 'A cancelled invoice stays on record, and its billing period cannot be billed again.' },
  },
}

const Total = ({ label, value, strong }) => (
  <div className={`flex justify-between gap-8 ${strong ? 'border-t border-slate-200 pt-2 font-semibold text-slate-900' : 'text-slate-600'}`}>
    <span>{label}</span><span>{formatMoney(value)}</span>
  </div>
)

export default function InvoiceDetailPage() {
  const id = Number(useParams().id)
  const toast = useToast()
  const qc = useQueryClient()
  const { user } = useAuth()
  const [paying, setPaying] = useState(false)
  const [pending, setPending] = useState(null)
  const { data: invoice, isLoading, isError } = useQuery({ queryKey: ['invoice', id], queryFn: () => invoicesApi.get(id) })
  const payments = useQuery({ queryKey: ['invoice-payments', id], queryFn: () => invoicesApi.payments(id), enabled: !!invoice })
  const act = useMutation({
    mutationFn: (action) => invoicesApi.act(id, action),
    onSuccess: (data) => {
      qc.setQueryData(['invoice', id], data)
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: () => qc.invalidateQueries({ queryKey: ['invoice', id] }),
  })
  const backTo = user.role === 'customer' ? '/portal/invoices' : '/invoices'

  const run = async (action) => {
    try {
      await act.mutateAsync(action)
      toast.success(`${ACTIONS[action].label} done`)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setPending(null)
    }
  }

  if (isLoading) return <div className="flex justify-center py-24"><Spinner className="h-8 w-8" /></div>
  if (isError || !invoice) {
    return (
      <EmptyState title="Invoice not found" message="It may not exist, or you may not have access."
        action={<Link to={backTo}><Button variant="secondary">Back to invoices</Button></Link>} />
    )
  }

  const allowed = invoice.allowed_actions
  const customer = invoice.customer_snapshot

  return (
    <div className="space-y-6">
      <PageHeader
        title={<span className="flex items-center gap-3">{invoice.invoice_number} <StatusBadge status={invoice.status} overdue={invoice.is_overdue} /></span>}
        subtitle={`${customer.name} · ${formatDate(invoice.period_start)} to ${formatDate(invoice.period_end)}`}
        actions={
          <>
            <Link to={backTo}><Button variant="ghost">← Back</Button></Link>
            <a href={invoicesApi.printUrl(id)} target="_blank" rel="noreferrer"><Button variant="secondary">Print</Button></a>
            {allowed.filter((a) => ACTIONS[a]).map((a) => (
              <Button key={a} variant={ACTIONS[a].variant} disabled={act.isPending} loading={act.isPending && act.variables === a}
                onClick={() => (ACTIONS[a].confirm ? setPending(a) : run(a))}>
                {ACTIONS[a].label}
              </Button>
            ))}
            {allowed.includes('pay') && <Button onClick={() => setPaying(true)}>Record payment</Button>}
          </>
        }
      />

      <section className="grid gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-3">
        <div className="text-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Billed to</div>
          <div className="mt-1 text-slate-900">{customer.name}</div>
          <div className="text-slate-500">{customer.email}</div>
        </div>
        <div className="text-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Invoice date</div>
          <div className="mt-1 text-slate-900">{formatDate(invoice.invoice_date)}</div>
        </div>
        <div className="text-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Due date</div>
          <div className="mt-1 text-slate-900">{formatDate(invoice.due_date)}</div>
        </div>
      </section>

      <section>
        <h2 className="mb-3 font-semibold text-slate-900">Lines</h2>
        <DataTable rows={invoice.lines}
          columns={[
            { key: 'description', header: 'Description' },
            { key: 'quantity', header: 'Qty' },
            { key: 'unit_price', header: 'Unit price', render: (l) => formatMoney(l.unit_price) },
            { key: 'discount_amount', header: 'Discount', render: (l) => formatMoney(l.discount_amount) },
            { key: 'tax', header: 'Tax', render: (l) => (l.tax_name ? `${l.tax_name}: ${formatMoney(l.tax_amount)}` : '—') },
            { key: 'line_total', header: 'Total', className: 'text-right', render: (l) => formatMoney(l.line_total) },
          ]} />
        <div className="mt-4 ml-auto max-w-xs space-y-2 text-sm">
          <Total label="Subtotal" value={invoice.subtotal} />
          <Total label="Discount" value={invoice.discount_total} />
          <Total label="Tax" value={invoice.tax_total} />
          <Total label="Total" value={invoice.total} strong />
          <Total label="Paid" value={invoice.amount_paid} />
          <Total label="Balance due" value={invoice.balance_due} strong />
        </div>
      </section>

      <section>
        <h2 className="mb-3 font-semibold text-slate-900">Payments</h2>
        <DataTable loading={payments.isLoading} rows={payments.data} empty={<EmptyState title="No payments yet" />}
          columns={[
            { key: 'payment_date', header: 'Date', render: (p) => formatDate(p.payment_date) },
            { key: 'method', header: 'Method', render: (p) => paymentMethodLabel(p.method) },
            { key: 'note', header: 'Note' },
            { key: 'amount', header: 'Amount', className: 'text-right', render: (p) => formatMoney(p.amount) },
          ]} />
      </section>

      {paying && <PaymentModal invoice={invoice} onClose={() => setPaying(false)} />}
      <ConfirmDialog open={!!pending} title={ACTIONS[pending]?.confirm?.title} message={ACTIONS[pending]?.confirm?.message} danger
        confirmLabel={ACTIONS[pending]?.label} loading={act.isPending} onConfirm={() => run(pending)} onCancel={() => setPending(null)} />
    </div>
  )
}
