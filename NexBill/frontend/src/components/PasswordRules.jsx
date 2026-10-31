import Icon from './Icon'
import { passwordRules } from '../schemas/auth'

export default function PasswordRules({ value = '' }) {
  return (
    <ul className="grid gap-1 text-xs" aria-label="Password rules">
      {passwordRules.map((r) => {
        const ok = r.test(value)
        return (
          <li key={r.key} className={`flex items-center gap-2 transition-colors ${ok ? 'text-emerald-700' : 'text-slate-500'}`}>
            <span className={`flex h-4 w-4 items-center justify-center rounded-full ${ok ? 'bg-emerald-100' : 'bg-slate-100'}`}>
              {ok && <Icon name="check" className="h-2.5 w-2.5" strokeWidth={3.5} />}
            </span>
            {r.label}
          </li>
        )
      })}
    </ul>
  )
}
