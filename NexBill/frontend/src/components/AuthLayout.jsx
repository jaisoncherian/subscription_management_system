import Logo from './Logo'
import Icon from './Icon'

const POINTS = [
  { icon: 'repeat', text: 'Quotes that turn into subscriptions in a few clicks' },
  { icon: 'invoice', text: 'Recurring invoices that can never bill a period twice' },
  { icon: 'trending', text: 'Revenue, overdue and MRR at a glance' },
]

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen bg-white lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-brand-900 p-12 text-white lg:flex">
        <div aria-hidden="true" className="absolute -right-32 -top-32 h-[28rem] w-[28rem] rounded-full bg-brand-600/50 blur-3xl" />
        <div aria-hidden="true" className="absolute -bottom-40 -left-24 h-[26rem] w-[26rem] rounded-full bg-brand-500/30 blur-3xl" />
        <Logo inverted className="relative" />
        <div className="relative max-w-lg">
          <h2 className="text-[2.5rem] font-semibold leading-[1.15] tracking-tight text-white">Subscriptions and billing, finally under control.</h2>
          <ul className="mt-8 space-y-4">
            {POINTS.map((p) => (
              <li key={p.icon} className="flex items-center gap-3 text-[15px] text-brand-100">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15"><Icon name={p.icon} /></span>
                {p.text}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-brand-200/80">© NexBill</p>
      </div>
      <div className="flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-sm animate-rise">
          <Logo className="mb-8 lg:hidden" />
          <h1 className="text-2xl font-semibold">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-slate-500">{subtitle}</p>}
          <div className="mt-7">{children}</div>
          {footer && <div className="mt-7 text-center text-sm text-slate-600">{footer}</div>}
        </div>
      </div>
    </div>
  )
}
