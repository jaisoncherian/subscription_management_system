import { useLocation } from 'react-router-dom'
import EmptyState from '../components/EmptyState'
import { NAV } from '../utils/nav'

export default function ComingSoon() {
  const { pathname } = useLocation()
  const item = NAV.find((n) => n.to === pathname)
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">{item?.label ?? 'Page'}</h1>
      <div className="rounded-xl border border-slate-200 bg-white">
        <EmptyState title="Coming next" message="This screen is built in the next batch." />
      </div>
    </div>
  )
}