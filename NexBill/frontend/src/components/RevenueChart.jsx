import { useState } from 'react'
import { formatMoney } from '../utils/format'

const SERIES = [
  { key: 'invoiced', label: 'Invoiced', color: '#4f46e5' },
  { key: 'collected', label: 'Collected', color: '#14b8a6' },
]
const HEIGHT = 'h-56'

const monthLabel = (period, withYear = false) => {
  const [y, m] = period.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-IN', withYear ? { month: 'long', year: 'numeric' } : { month: 'short' })
}

// Rounds up to 1, 2 or 5 times a power of ten, so the axis has tidy numbers.
function niceMax(value) {
  const power = 10 ** Math.floor(Math.log10(Math.max(value, 1)))
  const step = [1, 2, 5, 10].find((n) => n * power >= value)
  return step * power
}

const compact = (value) => `₹${new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(value)}`

export default function RevenueChart({ data = [] }) {
  const [hovered, setHovered] = useState(null)
  const max = niceMax(Math.max(1, ...data.flatMap((d) => [Number(d.invoiced), Number(d.collected)])))
  const ticks = [1, 0.75, 0.5, 0.25, 0]

  return (
    <div>
      <div className="mb-5 flex gap-5 text-xs text-slate-600">
        {SERIES.map((s) => (
          <span key={s.key} className="flex items-center gap-1.5">
            <i className="inline-block h-2.5 w-2.5 rounded-[3px]" style={{ background: s.color }} /> {s.label}
          </span>
        ))}
      </div>

      <div className="flex gap-3" aria-hidden="true">
        <div className={`${HEIGHT} flex w-12 flex-col justify-between text-right text-[11px] tabular-nums text-slate-400`}>
          {ticks.map((t) => <span key={t} className="-my-1.5 leading-3">{compact(max * t)}</span>)}
        </div>
        <div className="min-w-0 flex-1">
          <div className={`relative ${HEIGHT}`}>
            <div className="absolute inset-0 flex flex-col justify-between">
              {ticks.map((t) => <div key={t} className={`h-px ${t === 0 ? 'bg-slate-300' : 'bg-slate-100'}`} />)}
            </div>
            <div className="absolute inset-0 flex items-stretch">
              {data.map((d) => (
                <div key={d.period} className="relative flex flex-1 items-end justify-center gap-0.5 rounded-t-md transition-colors hover:bg-slate-100/70"
                  onMouseEnter={() => setHovered(d.period)} onMouseLeave={() => setHovered(null)}>
                  {SERIES.map((s) => (
                    <div key={s.key} className="w-[22%] max-w-7 rounded-t" style={{ background: s.color, height: `${(Number(d[s.key]) / max) * 100}%` }} />
                  ))}
                  {hovered === d.period && (
                    <div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 w-44 -translate-x-1/2 animate-fade rounded-lg border border-slate-200 bg-white p-2.5 text-xs shadow-pop">
                      <div className="mb-1.5 font-semibold text-slate-900">{monthLabel(d.period, true)}</div>
                      {SERIES.map((s) => (
                        <div key={s.key} className="flex items-center justify-between gap-3 py-0.5 text-slate-600">
                          <span className="flex items-center gap-1.5"><i className="inline-block h-2 w-2 rounded-sm" style={{ background: s.color }} />{s.label}</span>
                          <span className="font-medium tabular-nums text-slate-900">{formatMoney(d[s.key])}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="mt-2 flex">
            {data.map((d) => <span key={d.period} className="flex-1 text-center text-xs text-slate-500">{monthLabel(d.period)}</span>)}
          </div>
        </div>
      </div>

      <table className="sr-only">
        <caption>Revenue by month</caption>
        <thead><tr><th scope="col">Month</th>{SERIES.map((s) => <th key={s.key} scope="col">{s.label}</th>)}</tr></thead>
        <tbody>
          {data.map((d) => (
            <tr key={d.period}>
              <th scope="row">{monthLabel(d.period, true)}</th>
              {SERIES.map((s) => <td key={s.key}>{formatMoney(d[s.key])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
