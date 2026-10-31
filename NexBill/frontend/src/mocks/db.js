const pad = (n) => String(n).padStart(2, '0')
export const isoOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
export const iso = (offset = 0) => {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return isoOf(d)
}
export const toC = (s) => Math.round(parseFloat(s) * 100)
export const toM = (c) => (c / 100).toFixed(2)
export const nextId = (arr) => arr.reduce((m, x) => Math.max(m, x.id), 0) + 1
export const subNumber = (id) => `SUB-${String(id).padStart(4, '0')}`
export const invNumber = (id) => `INV-${String(id).padStart(4, '0')}`
export const custRef = (c) => ({ id: c.id, full_name: c.full_name, email: c.email })
export const planRef = (p) => ({ id: p.id, name: p.name, billing_period: p.billing_period, price: p.price })

const users = [
  { id: 1, email: 'admin@brightloop.com', password: 'Admin@12345', full_name: 'Asha Admin', role: 'admin', staff_function: null },
  { id: 2, email: 'staff@brightloop.com', password: 'Staff@12345', full_name: 'Sam Staff', role: 'staff', staff_function: 'sales_rep' },
  { id: 3, email: 'customer@brightloop.com', password: 'Customer@123', full_name: 'Cora Customer', role: 'customer', staff_function: null },
]

const customers = [
  { id: 3, full_name: 'Cora Customer', email: 'customer@brightloop.com', phone: '+91 98450 11122', created_on: iso(-120) },
  { id: 4, full_name: 'Ravi Menon', email: 'ravi@acme.in', phone: '+91 99950 22233', created_on: iso(-100) },
  { id: 5, full_name: 'Neha Kapoor', email: 'neha@globex.in', phone: '+91 98111 33344', created_on: iso(-60) },
  { id: 6, full_name: 'Tom Joseph', email: 'tom@initech.in', phone: '+91 97460 44455', created_on: iso(-20) },
]

const plan = (id, name, price, billing_period, extra = {}) => ({
  id, name, price, billing_period, billing_interval: 1, min_quantity: 1, valid_from: iso(-365), valid_to: null,
  is_auto_close: false, is_closable: true, is_pausable: true, is_renewable: true, is_active: true, ...extra,
})
const plans = [
  plan(1, 'Starter Monthly', '499.00', 'monthly'),
  plan(2, 'Pro Monthly', '1499.00', 'monthly'),
  plan(3, 'Business Yearly', '14999.00', 'yearly', { is_pausable: false, is_auto_close: true }),
]

const products = [
  {
    id: 1, name: 'CRM Suite', description: 'Customer relationship tools', product_type: 'service',
    sales_price: '1000.00', cost_price: '400.00', is_active: true,
    variants: [
      { id: 1, attribute: 'Support', value: 'Standard', extra_price: '0.00', is_active: true },
      { id: 2, attribute: 'Support', value: 'Premium', extra_price: '250.00', is_active: true },
    ],
  },
  { id: 2, name: 'Analytics Add-on', description: 'Dashboards and reports', product_type: 'service', sales_price: '500.00', cost_price: '150.00', is_active: true, variants: [] },
  { id: 3, name: 'Onboarding Kit', description: 'Setup and training', product_type: 'goods', sales_price: '750.00', cost_price: '300.00', is_active: true, variants: [] },
]

const taxes = [
  { id: 1, name: 'GST 18%', rate: '18.00', is_active: true },
  { id: 2, name: 'GST 5%', rate: '5.00', is_active: true },
]

const discounts = [
  { id: 1, code: 'WELCOME10', name: 'Welcome 10%', discount_type: 'percent', scope: 'subscription', value: '10.00', min_purchase: '0.00', min_quantity: 1, valid_from: iso(-30), valid_to: iso(60), usage_limit: 100, usage_count: 12, is_active: true, product_ids: [] },
  { id: 2, code: 'FLAT200', name: 'Flat 200 off', discount_type: 'fixed', scope: 'product', value: '200.00', min_purchase: '1000.00', min_quantity: 1, valid_from: iso(-10), valid_to: iso(90), usage_limit: 50, usage_count: 3, is_active: true, product_ids: [1] },
]

export const tplLine = (id, product, variant, tax, quantity) => ({
  id, product_id: product.id, product_name: product.name,
  variant_id: variant?.id ?? null, variant_label: variant ? `${variant.attribute}: ${variant.value}` : null,
  tax_id: tax?.id ?? null, quantity,
  unit_price: toM(toC(product.sales_price) + (variant ? toC(variant.extra_price) : 0)),
})

const templates = [
  { id: 1, name: 'Starter Package', plan_id: 1, validity_days: 30, is_active: true, lines: [tplLine(1, products[0], products[0].variants[0], taxes[0], 1)] },
  { id: 2, name: 'Pro Package', plan_id: 2, validity_days: 15, is_active: true, lines: [tplLine(1, products[0], products[0].variants[1], taxes[0], 2), tplLine(2, products[1], null, taxes[0], 1)] },
  { id: 3, name: 'Business Annual', plan_id: 3, validity_days: 30, is_active: true, lines: [tplLine(1, products[0], products[0].variants[1], taxes[0], 5), tplLine(2, products[2], null, taxes[1], 1)] },
]

export const linesFromTemplate = (t) =>
  t.lines.map((l, i) => ({
    id: i + 1, product_name: l.product_name, variant_label: l.variant_label, quantity: l.quantity,
    unit_price: l.unit_price, tax: taxes.find((x) => x.id === l.tax_id)?.name ?? null,
    amount: toM(toC(l.unit_price) * l.quantity),
  }))

const mkSub = (id, c, p, tpl, status, start, exp, next) => ({
  id, number: subNumber(id), customer: custRef(customers.find((x) => x.id === c)), plan: planRef(plans.find((x) => x.id === p)),
  status, start_date: start == null ? null : iso(start), expires_on: exp == null ? null : iso(exp),
  next_billing_date: next == null ? null : iso(next), notes: '', lines: linesFromTemplate(templates.find((t) => t.id === tpl)),
  created_on: iso(-30),
})
const subscriptions = [
  mkSub(1, 3, 2, 2, 'active', -90, 270, -2),
  mkSub(2, 4, 1, 1, 'active', -60, 300, 10),
  mkSub(3, 5, 3, 3, 'confirmed', 2, 365, null),
  mkSub(4, 6, 1, 1, 'quotation', null, 30, null),
  mkSub(5, 3, 1, 1, 'draft', null, null, null),
  mkSub(6, 4, 2, 2, 'paused', -120, 200, 20),
  mkSub(7, 5, 1, 1, 'closed', -200, -10, null),
]

export const mkInvoice = (id, sub, status, issueOff, dueOff, discount_c = 0) => ({
  id, number: invNumber(id), subscription_id: sub.id,
  customer_snapshot: { customer_id: sub.customer.id, full_name: sub.customer.full_name, email: sub.customer.email },
  status, issue_date: iso(issueOff), due_date: iso(dueOff), tax_rate: 18, discount_c,
  lines: sub.lines.map((l) => ({ description: l.product_name, quantity: l.quantity, unit_price: l.unit_price, amount: l.amount })),
})
const S = (id) => subscriptions.find((s) => s.id === id)
const invoices = [
  mkInvoice(1, S(1), 'paid', -95, -80),
  mkInvoice(2, S(1), 'paid', -65, -50),
  mkInvoice(3, S(1), 'paid', -35, -20),
  mkInvoice(4, S(1), 'confirmed', -5, 10),
  mkInvoice(5, S(2), 'confirmed', -40, -25),
  mkInvoice(6, S(2), 'confirmed', -20, -5),
  mkInvoice(7, S(6), 'draft', -1, 14),
  mkInvoice(8, S(2), 'paid', -70, -55),
  mkInvoice(9, S(7), 'cancelled', -150, -135),
]

export const db = { users, customers, plans, products, taxes, discounts, templates, subscriptions, invoices, payments: [] }

export function invoiceTotals(inv) {
  const sub = inv.lines.reduce((a, l) => a + toC(l.amount), 0)
  const tax = Math.round((sub * inv.tax_rate) / 100)
  const total = sub + tax - inv.discount_c
  const paid = db.payments.filter((p) => p.invoice_id === inv.id).reduce((a, p) => a + toC(p.amount), 0)
  return { sub, tax, total, paid }
}

let payId = 1
invoices.forEach((inv) => {
  if (inv.status === 'paid') {
    db.payments.push({ id: payId++, invoice_id: inv.id, invoice_number: inv.number, method: 'bank_transfer', amount: toM(invoiceTotals(inv).total), payment_date: inv.issue_date, note: '' })
  }
})
db.payments.push({ id: payId++, invoice_id: 4, invoice_number: invNumber(4), method: 'card', amount: '500.00', payment_date: iso(-3), note: 'Part payment' })