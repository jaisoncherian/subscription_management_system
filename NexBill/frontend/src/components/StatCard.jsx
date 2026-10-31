import Icon from './Icon'

const TONES = {
  default: { chip: 'bg-slate-100 text-slate-600', value: 'text-slate-900' },
  brand: { chip: 'bg-brand-50 text-brand-600', value: 'text-slate-900' },
  success: { chip: 'bg-emerald-50 text-emerald-600', value: 'text-slate-900' },
  danger: { chip: 'bg-rose-50 text-rose-600', value: 'text-rose-600' },
}

export default function StatCard({ label, value, hint, icon, tone = 'default', loading = false }) {
  const t = TONES[tone]
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[13px] font-medium text-slate-500">{label}</p>
        {icon && <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${t.chip}`}><Icon name={icon} /></span>}
      </div>
      {loading ? (
        <div className="mt-3 h-7 w-24 animate-pulse rounded bg-slate-100" />
      ) : (
        <p className={`mt-2 text-[22px] font-semibold tracking-tight tabular-nums ${t.value}`}>{value}</p>
      )}
      {hint && <p className="mt-0.5 text-xs text-slate-400">{hint}</p>}
    </div>
  )
}
