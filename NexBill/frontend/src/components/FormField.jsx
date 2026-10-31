import { forwardRef } from 'react'

const base =
  'block w-full rounded-lg border bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-100'

export function FormField({ label, htmlFor, error, hint, children }) {
  return (
    <div className="space-y-1">
      {label && <label htmlFor={htmlFor} className="block text-sm font-medium text-slate-700">{label}</label>}
      {children}
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-rose-600" role="alert">{error}</p>}
    </div>
  )
}

export const Input = forwardRef(function Input({ invalid, className = '', ...props }, ref) {
  return <input ref={ref} aria-invalid={!!invalid} className={`${base} ${invalid ? 'border-rose-400' : 'border-slate-300'} ${className}`} {...props} />
})

export const Select = forwardRef(function Select({ invalid, className = '', children, ...props }, ref) {
  return <select ref={ref} aria-invalid={!!invalid} className={`${base} ${invalid ? 'border-rose-400' : 'border-slate-300'} ${className}`} {...props}>{children}</select>
})

export const Textarea = forwardRef(function Textarea({ invalid, className = '', ...props }, ref) {
  return <textarea ref={ref} rows={3} aria-invalid={!!invalid} className={`${base} ${invalid ? 'border-rose-400' : 'border-slate-300'} ${className}`} {...props} />
})

export default FormField