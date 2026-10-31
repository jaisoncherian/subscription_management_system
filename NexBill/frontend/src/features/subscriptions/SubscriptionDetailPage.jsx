import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import PageHeader from '../../components/PageHeader'
import Button from '../../components/Button'
import DataTable from '../../components/DataTable'
import Icon from '../../components/Icon'
import StatusBadge from '../../components/StatusBadge'
import StatusStepper from '../../components/StatusStepper'
import ConfirmDialog from '../../components/ConfirmDialog'
import EmptyState from '../../components/EmptyState'
import Spinner from '../../components/Spinner'
import { useToast } from '../../components/Toast'
import { formatDate, formatMoney } from '../../utils/format'
import { sumMoney } from '../../utils/money'
import { SUB_ACTIONS } from '../../utils/subscriptionActions'
import { useSubscription, useSubscriptionAction } from './hooks'

const Info = ({ label, children }) => (
  <div>
    <dt className="eyebrow">{label}</dt>
    <dd className="mt-1.5 text-sm text-slate-900">{children || '—'}</dd>
  </div>
)

export default function SubscriptionDetailPage() {
  const id = Number(useParams().id)
  const toast = useToast()
  const { data: sub, isLoading, isError } = useSubscription(id)
  const act = useSubscriptionAction(id)
  const [pending, setPending] = useState(null)

  const run = async (a) => {
    try {
      await act.mutateAsync(a.action)
      toast.success(a.done)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setPending(null)
    }
  }
  const onClick = (a) => (a.confirm ? setPending(a) : run(a))

  if (isLoading) return <div className="flex justify-center py-24"><Spinner className="h-8 w-8" /></div>
  if (isError || !sub) {
    return (
      <EmptyState title="Subscription not found" message="It may not exist, or you may not have access."
        action={<Link to="/subscriptions"><Button variant="secondary">Back to subscriptions</Button></Link>} />
    )
  }

  const actions = (sub.allowed_actions ?? []).map((a) => SUB_ACTIONS[a]).filter(Boolean)

  return (
    <div className="space-y-5">
      <Link to="/subscriptions" className="inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-slate-900"><Icon name="arrowLeft" /> Subscriptions</Link>
      <PageHeader
        title={<span className="flex flex-wrap items-center gap-3">{sub.subscription_number} <StatusBadge status={sub.status} /></span>}
        subtitle={`${sub.customer_name} · ${sub.plan_name}`}
        actions={actions.map((a) => (
          <Button key={a.action} variant={a.variant} loading={act.isPending && act.variables === a.action} disabled={act.isPending} onClick={() => onClick(a)}>
            {a.label}
          </Button>
        ))}
      />

      <section className="card p-5"><StatusStepper status={sub.status} /></section>

      <section className="card p-6">
        <dl className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Info label="Customer">{sub.customer_name}<div className="text-xs text-slate-500">{sub.customer_email}</div></Info>
          <Info label="Plan">{sub.plan_name}<div className="text-xs capitalize text-slate-500">{sub.billing_period}</div></Info>
          <Info label="Next billing">{sub.next_billing_date && formatDate(sub.next_billing_date)}</Info>
          <Info label="Start date">{sub.start_date && formatDate(sub.start_date)}</Info>
          <Info label="Expires on">{sub.expires_on && formatDate(sub.expires_on)}</Info>
          <Info label="Notes (customer-visible)">{sub.notes}</Info>
        </dl>
      </section>

      <section>
        <h2 className="mb-3 text-[15px] font-semibold">Lines</h2>
        <DataTable
          rows={sub.lines}
          getRowKey={(l) => l.id ?? l.product_name}
          columns={[
            { key: 'product', header: 'Product', render: (l) => <><span className="font-medium text-slate-900">{l.product_name}</span>{l.variant_label && <div className="text-xs text-slate-500">{l.variant_label}</div>}</> },
            { key: 'quantity', header: 'Qty' },
            { key: 'unit_price', header: 'Unit price', render: (l) => formatMoney(l.unit_price) },
            { key: 'tax_name', header: 'Tax' },
            { key: 'amount', header: 'Amount', className: 'text-right', render: (l) => <span className="font-medium text-slate-900">{formatMoney(l.amount)}</span> },
          ]}
        />
        <p className="mt-3 text-right text-sm text-slate-500">Subtotal before tax and discounts <span className="ml-3 font-semibold tabular-nums text-slate-900">{formatMoney(sumMoney(sub.lines.map((l) => l.amount)))}</span></p>
      </section>

      <ConfirmDialog open={!!pending} title={pending?.confirm?.title} message={pending?.confirm?.message}
        danger={pending?.confirm?.danger} confirmLabel={pending?.label} loading={act.isPending}
        onConfirm={() => run(pending)} onCancel={() => setPending(null)} />
    </div>
  )
}
