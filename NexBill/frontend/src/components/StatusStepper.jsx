import { STATUS_STYLES } from '../utils/statuses'

const STEPS = ['draft', 'quotation', 'confirmed', 'active', 'closed']

export default function StatusStepper({ status }) {
  const idx = STEPS.indexOf(status === 'paused' ? 'active' : status)
  return (
    <ol className="flex items-start overflow-x-auto py-1" aria-label="Subscription progress">
      {STEPS.map((s, i) => {
        const done = i < idx
        const current = i === idx
        const circle = done ? 'bg-emerald-500 text-white' : current ? 'bg-brand-600 text-white ring-4 ring-brand-100' : 'bg-slate-200 text-slate-500'
        return (
          <li key={s} className="flex items-start" aria-current={current ? 'step' : undefined}>
            <div className="flex w-20 flex-col items-center gap-1 text-center">
              <span className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${circle}`}>{done ? '✓' : i + 1}</span>
              <span className={`text-xs ${current ? 'font-semibold text-slate-900' : 'text-slate-500'}`}>
                {status === 'paused' && s === 'active' ? 'Paused' : STATUS_STYLES[s].label}
              </span>
            </div>
            {i < STEPS.length - 1 && <div className={`mt-4 h-0.5 w-6 sm:w-12 ${i < idx ? 'bg-emerald-500' : 'bg-slate-200'}`} />}
          </li>
        )
      })}
    </ol>
  )
}