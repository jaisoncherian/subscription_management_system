import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/PageHeader'
import StatCard from '../../components/StatCard'
import RevenueChart from '../../components/RevenueChart'
import DataTable from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import Pagination from '../../components/Pagination'
import Spinner from '../../components/Spinner'
import { Input } from '../../components/FormField'
import { formatDate, formatMoney } from '../../utils/format'
import { useOverdue, useRevenue, useSummary } from './hooks'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [range, setRange] = useState({ date_from: '', date_to: '' })
  const [page, setPage] = useState(1)
  const summary = useSummary(range)
  const revenue = useRevenue(range)
  const overdue = useOverdue({ page, page_size: 5 })
  const s = summary.data
  const set = (key) => (e) => setRange((r) => ({ ...r, [key]: e.target.value }))

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Subscriptions and revenue at a glance"
        actions={
          <div className="flex items-center gap-2">
            <Input type="date" aria-label="From date" value={range.date_from} onChange={set('date_from')} className="w-auto" />
            <span className="text-sm text-slate-400">to</span>
            <Input type="date" aria-label="To date" value={range.date_to} onChange={set('date_to')} className="w-auto" />
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Active subscriptions" icon="repeat" tone="brand" value={s?.active_subscriptions} loading={summary.isLoading} />
        <StatCard label="MRR" icon="trending" tone="brand" value={formatMoney(s?.mrr)} hint="Monthly recurring revenue" loading={summary.isLoading} />
        <StatCard label="Revenue collected" icon="card" tone="success" value={formatMoney(s?.revenue_collected)} loading={summary.isLoading} />
        <StatCard label="Outstanding" icon="clock" value={formatMoney(s?.outstanding)} hint="Confirmed, not yet paid" loading={summary.isLoading} />
        <StatCard label="Overdue invoices" icon="alert" tone="danger" value={s?.overdue_count} loading={summary.isLoading} />
      </div>

      <section className="card mt-5 p-6">
        <h2 className="mb-4 text-[15px] font-semibold">Revenue by month</h2>
        {revenue.isLoading ? (
          <div className="flex h-72 items-center justify-center"><Spinner className="h-6 w-6" /></div>
        ) : revenue.data?.length ? (
          <RevenueChart data={revenue.data} />
        ) : (
          <EmptyState icon="trending" title="No revenue yet" message="Revenue appears here once invoices are confirmed." />
        )}
      </section>

      <section className="mt-7">
        <h2 className="mb-3 text-[15px] font-semibold">Overdue invoices</h2>
        <DataTable
          loading={overdue.isLoading}
          rows={overdue.data?.items}
          getRowKey={(r) => r.invoice_id}
          onRowClick={(r) => navigate(`/invoices/${r.invoice_id}`)}
          empty={<EmptyState icon="checkCircle" title="Nothing overdue" message="Every confirmed invoice is within its due date." />}
          columns={[
            { key: 'number', header: 'Invoice', render: (r) => <span className="font-medium text-slate-900">{r.number}</span> },
            { key: 'customer', header: 'Customer', render: (r) => r.customer },
            { key: 'due_date', header: 'Due', render: (r) => formatDate(r.due_date) },
            { key: 'days_overdue', header: 'Overdue by', render: (r) => <span className="font-medium text-rose-600">{r.days_overdue} days</span> },
            { key: 'balance', header: 'Balance', className: 'text-right', render: (r) => <span className="font-medium text-slate-900">{formatMoney(r.balance)}</span> },
          ]}
        />
        <Pagination page={page} perPage={5} total={overdue.data?.total ?? 0} onPageChange={setPage} />
      </section>
    </div>
  )
}
