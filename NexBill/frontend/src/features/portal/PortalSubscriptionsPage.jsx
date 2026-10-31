import EmptyState from '../../components/EmptyState'
import ListPage from '../../components/ListPage'
import StatusBadge from '../../components/StatusBadge'
import { portalApi } from '../../api/portal'
import { formatDate } from '../../utils/format'

export default function PortalSubscriptionsPage() {
  return (
    <ListPage title="My subscriptions" subtitle="Your plans and when they next bill" queryKey={['portal', 'subscriptions']}
      fetchPage={portalApi.subscriptions} getRowKey={(r) => r.subscription_id}
      empty={<EmptyState icon="repeat" title="No subscriptions yet" message="Your subscriptions appear here once our team sets them up." />}
      columns={[
        { key: 'number', header: 'Number', render: (r) => <span className="font-medium text-slate-900">{r.number}</span> },
        { key: 'plan_name', header: 'Plan' },
        { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
        { key: 'start_date', header: 'Started', render: (r) => formatDate(r.start_date) },
        { key: 'next_billing_date', header: 'Next billing', render: (r) => formatDate(r.next_billing_date) },
        { key: 'expires_on', header: 'Expires', render: (r) => formatDate(r.expires_on) },
      ]} />
  )
}
