import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/PageHeader'
import Button from '../../components/Button'
import DataTable from '../../components/DataTable'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import { Select } from '../../components/FormField'
import { formatDate } from '../../utils/format'
import { STATUS_STYLES } from '../../utils/statuses'
import { SUB_STATUSES } from '../../utils/subscriptionActions'
import { useSubscriptions } from './hooks'
import SubscriptionCreateModal from './SubscriptionCreateModal'

const PER_PAGE = 10

export default function SubscriptionsPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [creating, setCreating] = useState(false)
  const { data, isLoading, isError, error, refetch } = useSubscriptions({ page, page_size: PER_PAGE, status })

  return (
    <div>
      <PageHeader title="Subscriptions" subtitle="Quotations, active plans and renewals"
        actions={<Button onClick={() => setCreating(true)}>+ New subscription</Button>} />
      <div className="mb-4 max-w-xs">
        <label htmlFor="status-filter" className="sr-only">Filter by status</label>
        <Select id="status-filter" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
          <option value="">All statuses</option>
          {SUB_STATUSES.map((s) => <option key={s} value={s}>{STATUS_STYLES[s].label}</option>)}
        </Select>
      </div>
      {isError ? (
        <div role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
          {error.message} <button className="ml-2 underline" onClick={() => refetch()}>Retry</button>
        </div>
      ) : (
        <>
          <DataTable
            loading={isLoading}
            rows={data?.items}
            onRowClick={(r) => navigate(`/subscriptions/${r.id}`)}
            columns={[
              { key: 'number', header: 'Number', render: (r) => <span className="font-medium text-slate-900">{r.subscription_number}</span> },
              { key: 'customer', header: 'Customer', render: (r) => r.customer_name },
              { key: 'plan', header: 'Plan', render: (r) => r.plan_name },
              { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
              { key: 'next', header: 'Next billing', render: (r) => formatDate(r.next_billing_date) },
              { key: 'expires', header: 'Expires', render: (r) => formatDate(r.expires_on) },
            ]}
          />
          <Pagination page={page} perPage={PER_PAGE} total={data?.total ?? 0} onPageChange={setPage} />
        </>
      )}
      <SubscriptionCreateModal open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}