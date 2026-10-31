import { NavLink } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'
import { navFor } from '../utils/nav'

export default function Sidebar({ open, onClose }) {
  const { user } = useAuth()
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-slate-900 text-slate-300 transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="px-6 py-5 text-xl font-bold tracking-tight text-white">NexBill</div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-4" aria-label="Main">
          {navFor(user.role).map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                  isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
                }`}>
              <span aria-hidden="true">{n.icon}</span>{n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}