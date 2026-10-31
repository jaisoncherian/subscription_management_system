import { useNavigate } from 'react-router-dom'
import ListPage from '../../components/ListPage'
import { paymentsApi } from '../../api/invoices'
import { formatDate, formatMoney } from '../../utils/format'
import { paymentMethodLabel } from '../invoices/paymentMethods'

export default function PaymentsPage() {
  const navigate = useNavigate()
  return (
    <ListPage title="Payments" subtitle="Record a payment from its invoice" queryKey={['payments']} fetchPage={paymentsApi.list}
      onRowClick={(r) => navigate(`/invoices/${r.invoice_id}`)}
      columns={[
        { key: 'payment_date', header: 'Date', render: (r) => formatDate(r.payment_date) },
        { key: 'invoice_number', header: 'Invoice' },
        { key: 'customer_name', header: 'Customer' },
        { key: 'method', header: 'Method', render: (r) => paymentMethodLabel(r.method) },
        { key: 'amount', header: 'Amount', className: 'text-right', render: (r) => formatMoney(r.amount) },
      ]} />
  )
}
