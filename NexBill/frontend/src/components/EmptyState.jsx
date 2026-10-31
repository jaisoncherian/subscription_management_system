import Icon from './Icon'

export default function EmptyState({ title = 'Nothing here yet', message, action, icon = 'inbox' }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="mb-3.5 flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-500"><Icon name={icon} className="h-5 w-5" /></div>
      <h3 className="text-sm font-semibold">{title}</h3>
      {message && <p className="mt-1 max-w-sm text-sm text-slate-500">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
