import { formatMoney } from '../utils/format'

const monthLabel = (period) => {
  const [y, m] = period.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-IN', { month: 'short' })
}

export default function RevenueChart({ data = [] }) {
  const max = Math.max(1, ...data.flatMap((d) => [Number(d.invoiced), Number(d.collected)]))
  return (
    <div>
      <div className="flex h-52 items-stretch gap-3 sm:gap-6" role="img" aria-label="Revenue by month: invoiced and collected">
        {data.map((d) => (
          <div key={d.period} className="flex flex-1 flex-col">
            <div className="flex flex-1 items-end justify-center gap-1">
              <div title={`Invoiced ${formatMoney(d.invoiced)}`} className="w-1/3 max-w-8 rounded-t bg-brand-500" style={{ height: `${(Number(d.invoiced) / max) * 100}%` }} />
              <div title={`Collected ${formatMoney(d.collected)}`} className="w-1/3 max-w-8 rounded-t bg-emerald-400" style={{ height: `${(Number(d.collected) / max) * 100}%` }} />
            </div>
            <span className="mt-2 text-center text-xs text-slate-500">{monthLabel(d.period)}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-4 text-xs text-slate-600">
        <span className="flex items-center gap-1"><i className="inline-block h-2.5 w-2.5 rounded-sm bg-brand-500" /> Invoiced</span>
        <span className="flex items-center gap-1"><i className="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-400" /> Collected</span>
      </div>
    </div>
  )
}