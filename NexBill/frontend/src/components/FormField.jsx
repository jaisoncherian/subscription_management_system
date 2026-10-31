import { forwardRef } from 'react'

const base =
  'block w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-xs transition-colors placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-3 focus:ring-brand-500/15 disabled:bg-slate-100'
const border = (invalid) => (invalid ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/15' : 'border-slate-300/90 hover:border-slate-400')

export function FormField({ label, htmlFor, error, hint, children }) {
  return (
    <div className="space-y-1.5">
      {label && <label htmlFor={htmlFor} className="block text-[13px] font-medium text-slate-700">{label}</label>}
      {children}
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs font-medium text-rose-600" role="alert">{error}</p>}
    </div>
  )
}

export const Input = forwardRef(function Input({ invalid, className = '', ...props }, ref) {
  return <input ref={ref} aria-invalid={!!invalid} className={`${base} ${border(invalid)} ${className}`} {...props} />
})

export const Select = forwardRef(function Select({ invalid, className = '', children, ...props }, ref) {
  return <select ref={ref} aria-invalid={!!invalid} className={`${base} ${border(invalid)} ${className}`} {...props}>{children}</select>
})

export const Textarea = forwardRef(function Textarea({ invalid, className = '', ...props }, ref) {
  return <textarea ref={ref} rows={3} aria-invalid={!!invalid} className={`${base} ${border(invalid)} ${className}`} {...props} />
})

export default FormField
