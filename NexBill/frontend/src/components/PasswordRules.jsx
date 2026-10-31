import { passwordRules } from '../schemas/auth'

export default function PasswordRules({ value = '' }) {
  return (
    <ul className="space-y-1 text-xs" aria-label="Password rules">
      {passwordRules.map((r) => {
        const ok = r.test(value)
        return (
          <li key={r.key} className={ok ? 'text-emerald-600' : 'text-slate-500'}>
            {ok ? '✓' : '○'} {r.label}
          </li>
        )
      })}
    </ul>
  )
}