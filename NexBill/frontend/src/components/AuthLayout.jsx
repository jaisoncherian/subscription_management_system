export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-gradient-to-br from-brand-700 via-brand-600 to-indigo-500 p-12 text-white lg:flex">
        <div className="text-2xl font-bold tracking-tight">NexBill</div>
        <div>
          <h2 className="text-4xl font-semibold leading-tight">Subscriptions and billing,<br />finally under control.</h2>
          <p className="mt-4 max-w-md text-indigo-100">Plans, recurring invoices, payments and revenue reports in one place for Brightloop Software.</p>
        </div>
        <p className="text-sm text-indigo-200">© Brightloop Software</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-6 text-xl font-bold text-brand-600 lg:hidden">NexBill</div>
          <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          <div className="mt-6">{children}</div>
          {footer && <div className="mt-6 text-center text-sm text-slate-600">{footer}</div>}
        </div>
      </div>
    </div>
  )
}
