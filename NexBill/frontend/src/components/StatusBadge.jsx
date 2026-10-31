import { STATUS_STYLES } from '../utils/statuses'

export default function StatusBadge({ status, overdue = false }) {
  const key = overdue ? 'overdue' : status
  const s = STATUS_STYLES[key] ?? { label: key ?? '—', cls: 'bg-slate-100 text-slate-700' }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${s.cls}`}>
      {s.label}
    </span>
  )
}