import { useEffect } from 'react'
import Icon from './Icon'

export default function Modal({ open, onClose, title, children, footer }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 animate-fade bg-slate-900/45 backdrop-blur-[2px]" onClick={onClose} aria-hidden="true" />
      <div role="dialog" aria-modal="true" aria-label={title}
        className="relative flex max-h-[90vh] w-full max-w-lg animate-rise flex-col overflow-hidden rounded-2xl bg-white shadow-pop">
        <div className="flex items-center justify-between px-6 pb-2 pt-5">
          <h2 className="text-base font-semibold">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="-mr-1.5 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700">
            <Icon name="x" />
          </button>
        </div>
        <div className="overflow-y-auto px-6 py-3">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50/70 px-6 py-3.5">{footer}</div>}
      </div>
    </div>
  )
}
