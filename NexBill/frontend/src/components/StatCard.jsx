const TONES = { default: 'text-slate-900', danger: 'text-rose-600', success: 'text-emerald-600' }

export default function StatCard({ label, value, hint, tone = 'default', loading = false }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      {loading ? (
        <div className="mt-3 h-7 w-24 animate-pulse rounded bg-slate-200" />
      ) : (
        <p className={`mt-2 text-2xl font-semibold ${TONES[tone]}`}>{value}</p>
      )}
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  )
}