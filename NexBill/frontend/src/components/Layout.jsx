import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import Button from './Button'
import { useAuth } from '../features/auth/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const onLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur">
          <button className="rounded p-2 text-slate-600 hover:bg-slate-100 lg:hidden" aria-label="Open menu" onClick={() => setOpen(true)}>☰</button>
          <div className="ml-auto flex items-center gap-3">
            <div className="text-right leading-tight">
              <div className="text-sm font-medium">{user.full_name}</div>
              <div className="text-xs capitalize text-slate-500">{user.role}</div>
            </div>
            <Button variant="secondary" onClick={onLogout}>Log out</Button>
          </div>
        </header>
        <main className="p-4 sm:p-6"><Outlet /></main>
      </div>
    </div>
  )
}