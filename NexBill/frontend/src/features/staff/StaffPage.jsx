import ResourcePage from '../../components/ResourcePage'
import { staffApi } from '../../api/catalog'

const FUNCTIONS = [
  { value: 'sales_rep', label: 'Sales rep' },
  { value: 'finance_lead', label: 'Finance lead' },
  { value: 'support', label: 'Support' },
]
const functionLabel = (value) => FUNCTIONS.find((f) => f.value === value)?.label ?? '—'

export default function StaffPage() {
  return (
    <ResourcePage title="Staff" subtitle="Accounts for your team" noun="staff account" queryKey={['staff']} api={staffApi}
      getRowLabel={(r) => r.full_name}
      columns={[
        { key: 'full_name', header: 'Name' },
        { key: 'email', header: 'Email' },
        { key: 'staff_function', header: 'Function', render: (r) => functionLabel(r.staff_function) },
      ]}
      fields={[
        { name: 'full_name', label: 'Full name' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'password', label: 'Password', type: 'password', hint: 'More than 8 characters, with upper case, lower case and a special character' },
        { name: 'staff_function', label: 'Function', type: 'select', options: FUNCTIONS },
      ]} />
  )
}
