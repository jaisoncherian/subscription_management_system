import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Icon from '../components/Icon'
import { useAuth, homeFor } from '../features/auth/AuthContext'

export default function ForbiddenPage() {
  const { user } = useAuth()
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-500"><Icon name="lock" className="h-6 w-6" /></div>
      <h1 className="text-xl font-semibold">Not allowed</h1>
      <p className="mt-1 text-sm text-slate-500">You do not have access to this page.</p>
      <Link to={homeFor(user?.role)} className="mt-6"><Button>Go to my home page</Button></Link>
    </div>
  )
}