import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/PageHeader'
import StatCard from '../../components/StatCard'
import RevenueChart from '../../components/RevenueChart'
import DataTable from '../../components/DataTable'
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
          <>
            <label className="text-sm text-slate-600">
              From <Input type="date" value={range.date_from} onChange={set('date_from')} className="ml-1 inline-block w-auto" />
            </label>
            <label className="text-sm text-slate-600">
              To <Input type="date" value={range.date_to} onChange={set('date_to')} className="ml-1 inline-block w-auto" />
            </label>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Active subscriptions" value={s?.active_subscriptions} loading={summary.isLoading} />
        <StatCard label="MRR" value={formatMoney(s?.mrr)} hint="Monthly recurring revenue" loading={summary.isLoading} />
        <StatCard label="Revenue collected" value={formatMoney(s?.revenue_collected)} tone="success" loading={summary.isLoading} />
        <StatCard label="Outstanding" value={formatMoney(s?.outstanding)} loading={summary.isLoading} />
        <StatCard label="Overdue invoices" value={s?.overdue_count} tone="danger" loading={summary.isLoading} />
      </div>

      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 font-semibold text-slate-900">Revenue by month</h2>
        {revenue.isLoading ? (
          <div className="flex h-52 items-center justify-center"><Spinner className="h-6 w-6" /></div>
        ) : (
          <RevenueChart data={revenue.data} />
        )}
      </section>

      <section className="mt-6">
        <h2 className="mb-3 font-semibold text-slate-900">Overdue invoices</h2>
        <DataTable
          loading={overdue.isLoading}
          rows={overdue.data?.items}
          getRowKey={(r) => r.invoice_id}
          onRowClick={(r) => navigate(`/invoices/${r.invoice_id}`)}
          columns={[
            { key: 'number', header: 'Invoice' },
            { key: 'customer', header: 'Customer', render: (r) => r.customer },
            { key: 'due_date', header: 'Due', render: (r) => formatDate(r.due_date) },
            { key: 'days_overdue', header: 'Days overdue', render: (r) => <span className="font-medium text-rose-600">{r.days_overdue} days</span> },
            { key: 'balance', header: 'Balance', className: 'text-right', render: (r) => formatMoney(r.balance) },
          ]}
        />
        <Pagination page={page} perPage={5} total={overdue.data?.total ?? 0} onPageChange={setPage} />
      </section>
    </div>
  )
}