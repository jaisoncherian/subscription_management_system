import { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../../api/auth'
import { setUnauthorizedHandler } from '../../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null))
    authApi.me().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false))
  }, [])

  const login = async (creds) => {
    const u = await authApi.login(creds)
    setUser(u)
    return u
  }
  const logout = async () => {
    try { await authApi.logout() } catch { /* ignore */ }
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext)
// eslint-disable-next-line react-refresh/only-export-components
export const homeFor = (role) => (role === 'customer' ? '/portal' : '/dashboard')