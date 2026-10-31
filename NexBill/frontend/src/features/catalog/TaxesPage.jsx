import ResourcePage from '../../components/ResourcePage'
import { taxesApi } from '../../api/catalog'

export default function TaxesPage() {
  return (
    <ResourcePage title="Taxes" subtitle="Rates applied per invoice line" noun="tax" queryKey={['taxes']} api={taxesApi}
      getRowLabel={(r) => r.name}
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'rate', header: 'Rate', render: (r) => `${r.rate}%` },
      ]}
      fields={[
        { name: 'name', label: 'Name' },
        { name: 'rate', label: 'Rate (%)', type: 'money', hint: 'Between 0 and 100' },
      ]} />
  )
}
