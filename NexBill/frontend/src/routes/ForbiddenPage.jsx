import { Link } from 'react-router-dom'
import Button from '../components/Button'
import { useAuth, homeFor } from '../features/auth/AuthContext'

export default function ForbiddenPage() {
  const { user } = useAuth()
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="text-6xl font-bold text-brand-600">403</div>
      <h1 className="mt-2 text-xl font-semibold">Not allowed</h1>
      <p className="mt-1 text-sm text-slate-500">You do not have access to this page.</p>
      <Link to={homeFor(user?.role)} className="mt-6"><Button>Go to my home page</Button></Link>
    </div>
  )
}