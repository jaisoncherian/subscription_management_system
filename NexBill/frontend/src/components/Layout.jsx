import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import Icon from './Icon'
import Logo from './Logo'
import Sidebar from './Sidebar'
import { useAuth } from '../features/auth/AuthContext'

export default function Layout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const onLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen">
      <Sidebar open={open} onClose={() => setOpen(false)} onLogout={onLogout} />
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur lg:hidden">
          <Logo />
          <button type="button" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100" aria-label="Open menu" onClick={() => setOpen(true)}>
            <Icon name="menu" className="h-5 w-5" />
          </button>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-8"><Outlet /></main>
      </div>
    </div>
  )
}
