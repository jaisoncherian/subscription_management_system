import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from '../components/Layout'
import LoginPage from '../features/auth/LoginPage'
import SignupPage from '../features/auth/SignupPage'
import ForgotPasswordPage from '../features/auth/ForgotPasswordPage'
import ResetPasswordPage from '../features/auth/ResetPasswordPage'
import DiscountsPage from '../features/catalog/DiscountsPage'
import PlansPage from '../features/catalog/PlansPage'
import ProductsPage from '../features/catalog/ProductsPage'
import TaxesPage from '../features/catalog/TaxesPage'
import CustomersPage from '../features/customers/CustomersPage'
import InvoiceDetailPage from '../features/invoices/InvoiceDetailPage'
import InvoicesPage from '../features/invoices/InvoicesPage'
import PaymentsPage from '../features/payments/PaymentsPage'
import PortalInvoicesPage from '../features/portal/PortalInvoicesPage'
import PortalSubscriptionsPage from '../features/portal/PortalSubscriptionsPage'
import DashboardPage from '../features/reports/DashboardPage'
import StaffPage from '../features/staff/StaffPage'
import SubscriptionsPage from '../features/subscriptions/SubscriptionsPage'
import SubscriptionDetailPage from '../features/subscriptions/SubscriptionDetailPage'
import TemplatesPage from '../features/templates/TemplatesPage'
import { HomeRedirect, PublicOnly, RequireAuth, RequireRole } from './guards'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route element={<PublicOnly />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      </Route>
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route element={<RequireRole roles={['admin', 'staff']} />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/subscriptions" element={<SubscriptionsPage />} />
            <Route path="/subscriptions/:id" element={<SubscriptionDetailPage />} />
            <Route path="/invoices" element={<InvoicesPage />} />
            <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
            <Route path="/payments" element={<PaymentsPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/templates" element={<TemplatesPage />} />
            <Route path="/products" element={<ProductsPage />} />
          </Route>
          <Route element={<RequireRole roles={['admin']} />}>
            <Route path="/plans" element={<PlansPage />} />
            <Route path="/taxes" element={<TaxesPage />} />
            <Route path="/discounts" element={<DiscountsPage />} />
            <Route path="/staff" element={<StaffPage />} />
          </Route>
          <Route element={<RequireRole roles={['customer']} />}>
            <Route path="/portal" element={<PortalSubscriptionsPage />} />
            <Route path="/portal/invoices" element={<PortalInvoicesPage />} />
            <Route path="/portal/invoices/:id" element={<InvoiceDetailPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
