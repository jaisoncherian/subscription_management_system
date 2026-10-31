import Spinner from './Spinner'

const VARIANTS = {
  primary: 'bg-brand-600 text-white shadow-sm hover:bg-brand-700 active:bg-brand-800',
  secondary: 'bg-white text-slate-700 border border-slate-300/80 shadow-xs hover:bg-slate-50 hover:border-slate-300 active:bg-slate-100',
  danger: 'bg-white text-rose-700 border border-rose-200 shadow-xs hover:bg-rose-50 hover:border-rose-300 active:bg-rose-100',
  'danger-solid': 'bg-rose-600 text-white shadow-sm hover:bg-rose-700 active:bg-rose-800',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
}

export default function Button({ variant = 'primary', loading = false, className = '', children, ...props }) {
  return (
    <button
      type="button"
      {...props}
      disabled={loading || props.disabled}
      className={`inline-flex h-9 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3.5 text-[13.5px] font-medium transition-colors
        focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2
        disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
    >
      {loading && <Spinner className="h-4 w-4 text-current" />}
      {children}
    </button>
  )
}
