export default function Logo({ inverted = false, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <span className={`flex h-8 w-8 items-center justify-center rounded-[10px] shadow-sm ${inverted ? 'bg-white/15 ring-1 ring-white/25' : 'bg-gradient-to-br from-brand-500 to-brand-700'}`}>
        <svg viewBox="0 0 32 32" className="h-5 w-5" aria-hidden="true">
          <path d="M9 23V9l14 14V9" fill="none" stroke="#fff" strokeWidth="3.25" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <span className={`text-[17px] font-semibold tracking-tight ${inverted ? 'text-white' : 'text-slate-900'}`}>NexBill</span>
    </span>
  )
}
