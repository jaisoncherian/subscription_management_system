import { useNavigate } from 'react-router-dom'
import EmptyState from '../../components/EmptyState'
import ListPage from '../../components/ListPage'
import StatusBadge from '../../components/StatusBadge'
import { portalApi } from '../../api/portal'
import { formatDate, formatMoney, todayISO } from '../../utils/format'

export default function PortalInvoicesPage() {
  const navigate = useNavigate()
  return (
    <ListPage title="My invoices" subtitle="View or print your invoices" queryKey={['portal', 'invoices']}
      fetchPage={portalApi.invoices} getRowKey={(r) => r.invoice_id} onRowClick={(r) => navigate(`/portal/invoices/${r.invoice_id}`)}
      empty={<EmptyState title="No invoices yet" />}
      columns={[
        { key: 'number', header: 'Number', render: (r) => <span className="font-medium text-slate-900">{r.number}</span> },
        { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} overdue={r.status === 'confirmed' && r.due_date < todayISO()} /> },
        { key: 'due_date', header: 'Due', render: (r) => formatDate(r.due_date) },
        { key: 'total', header: 'Total', className: 'text-right', render: (r) => formatMoney(r.total) },
        { key: 'balance', header: 'Balance', className: 'text-right', render: (r) => formatMoney(r.balance) },
      ]} />
  )
}
