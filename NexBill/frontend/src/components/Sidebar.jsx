import { NavLink } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'
import { navFor } from '../utils/nav'
import Icon from './Icon'
import Logo from './Logo'

const initials = (name = '') => name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase()

export default function Sidebar({ open, onClose, onLogout }) {
  const { user } = useAuth()
  return (
    <>
      {open && <div className="fixed inset-0 z-30 animate-fade bg-slate-900/40 backdrop-blur-[2px] lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200/80 bg-white transition-transform duration-200 lg:translate-x-0 ${open ? 'translate-x-0 shadow-pop' : '-translate-x-full'}`}>
        <div className="flex h-16 items-center px-5"><Logo /></div>
        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-3" aria-label="Main">
          {navFor(user.role).map((section) => (
            <div key={section.group}>
              <p className="eyebrow mb-1.5 px-3 text-slate-400">{section.group}</p>
              <div className="space-y-0.5">
                {section.items.map((n) => (
                  <NavLink key={n.to} to={n.to} end={n.end} onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-[13.5px] font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                        isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      }`}>
                    <Icon name={n.icon} className="h-[18px] w-[18px]" />{n.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="flex items-center gap-3 border-t border-slate-200/80 p-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">{initials(user.full_name)}</span>
          <div className="min-w-0 flex-1 leading-tight">
            <div className="truncate text-[13px] font-medium text-slate-900">{user.full_name}</div>
            <div className="text-xs capitalize text-slate-500">{user.role}</div>
          </div>
          <button type="button" onClick={onLogout} aria-label="Log out" title="Log out"
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500">
            <Icon name="logout" />
          </button>
        </div>
      </aside>
    </>
  )
}
