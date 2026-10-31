import { Navigate, Outlet, useLocation } from 'react-router-dom'
import Spinner from '../components/Spinner'
import { useAuth, homeFor } from '../features/auth/AuthContext'
import ForbiddenPage from './ForbiddenPage'

const FullPageSpinner = () => <div className="flex min-h-screen items-center justify-center"><Spinner className="h-8 w-8" /></div>

export function RequireAuth() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <FullPageSpinner />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}

export function RequireRole({ roles }) {
  const { user } = useAuth()
  return roles.includes(user.role) ? <Outlet /> : <ForbiddenPage />
}

export function PublicOnly() {
  const { user, loading } = useAuth()
  if (loading) return <FullPageSpinner />
  if (user) return <Navigate to={homeFor(user.role)} replace />
  return <Outlet />
}

export function HomeRedirect() {
  const { user, loading } = useAuth()
  if (loading) return <FullPageSpinner />
  return <Navigate to={user ? homeFor(user.role) : '/login'} replace />
}