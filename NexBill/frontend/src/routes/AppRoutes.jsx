import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from '../components/Layout'
import LoginPage from '../features/auth/LoginPage'
import SignupPage from '../features/auth/SignupPage'
import ForgotPasswordPage from '../features/auth/ForgotPasswordPage'
import ResetPasswordPage from '../features/auth/ResetPasswordPage'
import { HomeRedirect, PublicOnly, RequireAuth, RequireRole } from './guards'
import ComingSoon from './ComingSoon'

const STAFF_PATHS = ['dashboard', 'subscriptions', 'invoices', 'payments', 'customers', 'templates', 'products']
const ADMIN_PATHS = ['plans', 'taxes', 'discounts', 'staff']

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
            {STAFF_PATHS.map((p) => <Route key={p} path={`/${p}`} element={<ComingSoon />} />)}
          </Route>
          <Route element={<RequireRole roles={['admin']} />}>
            {ADMIN_PATHS.map((p) => <Route key={p} path={`/${p}`} element={<ComingSoon />} />)}
          </Route>
          <Route element={<RequireRole roles={['customer']} />}>
            <Route path="/portal" element={<ComingSoon />} />
            <Route path="/portal/invoices" element={<ComingSoon />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}