import ListPage from '../../components/ListPage'
import { customersApi } from '../../api/customers'

export default function CustomersPage() {
  return (
    <ListPage title="Customers" subtitle="Customers create their own accounts when they sign up" queryKey={['customers']} fetchPage={customersApi.list}
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'email', header: 'Email' },
      ]} />
  )
}
