import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/Button'
import { Select } from '../../components/FormField'
import ListPage from '../../components/ListPage'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../components/Toast'
import { billingApi, invoicesApi } from '../../api/invoices'
import { formatDate, formatMoney } from '../../utils/format'
import { useAuth } from '../auth/AuthContext'

const STATUSES = [
  { value: '', label: 'All invoices' },
  { value: 'draft', label: 'Draft' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'paid', label: 'Paid' },
  { value: 'cancelled', label: 'Cancelled' },
]

export default function InvoicesPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const qc = useQueryClient()
  const { user } = useAuth()
  const [filter, setFilter] = useState('')
  const billing = useMutation({
    mutationFn: billingApi.run,
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['reports'] })
      if (s.failures) toast.error(`Billing finished with ${s.failures} failures. Check the logs.`)
      else toast.success(`Billing finished: ${s.invoices_created} invoices created.`)
    },
    onError: (err) => toast.error(err.message),
  })
  const params = filter === 'overdue' ? { overdue: 'true' } : { status: filter }

  return (
    <ListPage title="Invoices" subtitle="Created by the billing run, then confirmed and paid" queryKey={['invoices']} fetchPage={invoicesApi.list} params={params}
      actions={user.role === 'admin' && <Button loading={billing.isPending} onClick={() => billing.mutate()}>Run billing</Button>}
      onRowClick={(r) => navigate(`/invoices/${r.id}`)}
      columns={[
        { key: 'invoice_number', header: 'Number', render: (r) => <span className="font-medium text-slate-900">{r.invoice_number}</span> },
        { key: 'customer', header: 'Customer', render: (r) => r.customer_snapshot?.name },
        { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} overdue={r.is_overdue} /> },
        { key: 'invoice_date', header: 'Date', render: (r) => formatDate(r.invoice_date) },
        { key: 'due_date', header: 'Due', render: (r) => formatDate(r.due_date) },
        { key: 'total', header: 'Total', className: 'text-right', render: (r) => formatMoney(r.total) },
        { key: 'balance_due', header: 'Balance', className: 'text-right', render: (r) => formatMoney(r.balance_due) },
      ]}>
      <div className="mb-4 max-w-xs">
        <label htmlFor="invoice-filter" className="sr-only">Filter by status</label>
        <Select id="invoice-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
          {STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </Select>
      </div>
    </ListPage>
  )
}
