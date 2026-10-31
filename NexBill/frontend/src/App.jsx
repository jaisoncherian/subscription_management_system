import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider } from './features/auth/AuthContext'
import AppRoutes from './routes/AppRoutes'

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ErrorBoundary>
  )
}