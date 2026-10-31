import ResourcePage from '../../components/ResourcePage'
import { plansApi } from '../../api/catalog'

const PERIODS = ['daily', 'weekly', 'monthly', 'yearly'].map((p) => ({ value: p, label: p[0].toUpperCase() + p.slice(1) }))
const yesNo = (value) => (value ? 'Yes' : 'No')

export default function PlansPage() {
  return (
    <ResourcePage title="Plans" subtitle="How often customers are billed, and what they can change" noun="plan" queryKey={['plans']} api={plansApi}
      getRowLabel={(r) => r.name}
      defaults={{ billing_period: 'monthly', is_closable: true }}
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'billing_period', header: 'Billing', render: (r) => `Every ${r.billing_interval > 1 ? `${r.billing_interval} ` : ''}${r.billing_period}` },
        { key: 'min_quantity', header: 'Min qty' },
        { key: 'is_pausable', header: 'Pausable', render: (r) => yesNo(r.is_pausable) },
        { key: 'is_renewable', header: 'Renewable', render: (r) => yesNo(r.is_renewable) },
        { key: 'is_closable', header: 'Closable', render: (r) => yesNo(r.is_closable) },
      ]}
      fields={[
        { name: 'name', label: 'Name' },
        { name: 'billing_period', label: 'Billing period', type: 'select', options: PERIODS },
        { name: 'billing_interval', label: 'Bill every', type: 'number', hint: 'Number of periods. Defaults to 1' },
        { name: 'min_quantity', label: 'Minimum quantity', type: 'number', hint: 'Defaults to 1' },
        { name: 'valid_from', label: 'Valid from', type: 'date' },
        { name: 'valid_to', label: 'Valid to', type: 'date' },
        { name: 'is_pausable', label: 'Customers can pause', type: 'checkbox' },
        { name: 'is_renewable', label: 'Can be renewed', type: 'checkbox' },
        { name: 'is_closable', label: 'Can be closed', type: 'checkbox' },
        { name: 'is_auto_close', label: 'Close automatically on expiry', type: 'checkbox' },
      ]} />
  )
}
