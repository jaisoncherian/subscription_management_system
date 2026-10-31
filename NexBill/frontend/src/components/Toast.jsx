import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import Icon from './Icon'

const ToastContext = createContext(null)
const STYLES = {
  success: { icon: 'checkCircle', color: 'text-emerald-500' },
  error: { icon: 'alert', color: 'text-rose-500' },
  info: { icon: 'alert', color: 'text-slate-500' },
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const push = useCallback((type, message) => {
    const id = crypto.randomUUID()
    setToasts((t) => [...t, { id, type, message }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000)
  }, [])

  const api = useMemo(() => ({
    success: (m) => push('success', m),
    error: (m) => push('error', m),
    info: (m) => push('info', m),
  }), [push])

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[60] flex w-80 flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto flex animate-rise items-start gap-2.5 rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-sm font-medium text-slate-800 shadow-pop">
            <Icon name={STYLES[t.type].icon} className={`mt-px h-[18px] w-[18px] ${STYLES[t.type].color}`} />
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(ToastContext)
