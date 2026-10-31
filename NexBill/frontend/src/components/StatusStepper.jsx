import Icon from './Icon'
import { STATUS_STYLES } from '../utils/statuses'

const STEPS = ['draft', 'quotation', 'confirmed', 'active', 'closed']

export default function StatusStepper({ status }) {
  const idx = STEPS.indexOf(status === 'paused' ? 'active' : status)
  // A closed subscription has finished, so its last step shows as done too.
  const finished = status === 'closed'
  return (
    <ol className="flex items-center overflow-x-auto" aria-label="Subscription progress">
      {STEPS.map((s, i) => {
        const done = i < idx || (finished && i === idx)
        const current = i === idx && !finished
        const circle = done
          ? 'bg-brand-600 text-white'
          : current
            ? 'bg-white text-brand-700 ring-2 ring-brand-600'
            : 'bg-white text-slate-400 ring-1 ring-slate-300'
        return (
          <li key={s} className={`flex items-center ${i < STEPS.length - 1 ? 'flex-1' : ''}`} aria-current={current ? 'step' : undefined}>
            <div className="flex items-center gap-2.5">
              <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${circle}`}>
                {done ? <Icon name="check" className="h-3.5 w-3.5" strokeWidth={3} /> : i + 1}
              </span>
              <span className={`whitespace-nowrap text-[13px] ${current || done ? 'font-medium text-slate-900' : 'text-slate-500'}`}>
                {status === 'paused' && s === 'active' ? 'Paused' : STATUS_STYLES[s].label}
              </span>
            </div>
            {i < STEPS.length - 1 && <div className={`mx-3 h-px min-w-6 flex-1 ${i < idx ? 'bg-brand-600' : 'bg-slate-200'}`} />}
          </li>
        )
      })}
    </ol>
  )
}
