import { ApiError } from '../api/client'
import { db, iso, isoOf, toC, toM, nextId, subNumber, custRef, planRef, linesFromTemplate, mkInvoice, invoiceTotals, tplLine } from './db'

const delay = (ms = 250) => new Promise((r) => setTimeout(r, ms))
const KEY = 'mock_user_id'
const current = () => db.users.find((u) => u.id === Number(sessionStorage.getItem(KEY)))
const publicUser = ({ password, ...u }) => u // eslint-disable-line no-unused-vars

function fail(status, code, message, fields = {}) {
  throw new ApiError({ code, message, fields }, status)
}
const requireStaff = (u) => u.role === 'customer' && fail(403, 'forbidden', 'You do not have access.')
const requireAdmin = (u) => u.role !== 'admin' && fail(403, 'forbidden', 'You do not have access.')
const invalid = (fields) => fail(422, 'validation_error', 'The submitted data is invalid.', fields)

function paginate(items, params = {}) {
  const per = Math.min(Number(params.per_page) || 20, 100)
  const page = Number(params.page) || 1
  return { items: items.slice((page - 1) * per, page * per), total: items.length, page, per_page: per }
}

function addPeriod(dateStr, period) {
  const [y, m, d] = dateStr.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  if (period === 'daily') dt.setDate(dt.getDate() + 1)
  else if (period === 'weekly') dt.setDate(dt.getDate() + 7)
  else if (period === 'monthly') dt.setMonth(dt.getMonth() + 1)
  else dt.setFullYear(dt.getFullYear() + 1)
  return isoOf(dt)
}

/* ---------- auth ---------- */
function auth(method, action, body = {}) {
  switch (`${method} ${action}`) {
    case 'POST login': {
      const u = db.users.find((x) => x.email === body.email && x.password === body.password)
      if (!u) fail(401, 'invalid_credentials', 'Invalid email or password.')
      sessionStorage.setItem(KEY, String(u.id))
      return publicUser(u)
    }
    case 'POST register': {
      if (db.users.some((x) => x.email === body.email)) fail(409, 'email_taken', 'This email is already registered.', { email: ['This email is already registered.'] })
      const id = Math.max(nextId(db.users), nextId(db.customers))
      const u = { id, email: body.email, password: body.password, full_name: body.full_name, role: 'customer', staff_function: null }
      db.users.push(u)
      db.customers.push({ id, full_name: u.full_name, email: u.email, phone: '', created_on: iso(0) })
      return publicUser(u)
    }
    case 'POST logout':
      sessionStorage.removeItem(KEY)
      return { message: 'Logged out' }
    case 'GET me': {
      const u = current()
      if (!u) fail(401, 'unauthorized', 'Not logged in.')
      return publicUser(u)
    }
    case 'POST forgot-password':
      return { message: 'If that email exists, a reset link has been sent.' }
    case 'POST reset-password':
      if (body.token === 'expired') fail(400, 'invalid_reset_token', 'This reset link is invalid or has expired.')
      return { message: 'Password updated.' }
    default:
      return fail(404, 'not_found', 'Not found.')
  }
}

/* ---------- subscriptions ---------- */
const TRANSITIONS = {
  'send-quotation': { from: ['draft'], to: 'quotation' },
  confirm: { from: ['quotation'], to: 'confirmed' },
  activate: { from: ['confirmed'], to: 'active' },
  pause: { from: ['active'], to: 'paused' },
  resume: { from: ['paused'], to: 'active' },
  renew: { from: ['active'], to: 'active' },
  close: { from: ['active', 'paused'], to: 'closed' },
}
const planBlock = (what) => fail(409, 'action_not_allowed_by_plan', `This plan does not allow ${what}.`)

function subscriptions(user, method, id, action, body = {}, params = {}) {
  if (!id) {
    if (method === 'GET') {
      let items = [...db.subscriptions].reverse()
      if (user.role === 'customer') items = items.filter((s) => s.customer.id === user.id)
      if (params.status) items = items.filter((s) => s.status === params.status)
      if (params.customer_id) items = items.filter((s) => s.customer.id === Number(params.customer_id))
      return paginate(items, params)
    }
    requireStaff(user)
    const customer = db.customers.find((c) => c.id === body.customer_id)
    const tpl = db.templates.find((t) => t.id === body.template_id)
    const fields = {}
    if (!customer) fields.customer_id = ['Choose a valid customer.']
    if (!tpl) fields.template_id = ['Choose a valid template.']
    if (body.start_date && body.expires_on && body.expires_on < body.start_date) fields.expires_on = ['Expiry must be on or after the start date.']
    if (Object.keys(fields).length) invalid(fields)
    if (!tpl.is_active) fail(409, 'catalog_item_inactive', 'This template is no longer active.')
    const newId = nextId(db.subscriptions)
    const sub = {
      id: newId, number: subNumber(newId), customer: custRef(customer),
      plan: planRef(db.plans.find((p) => p.id === tpl.plan_id)), status: 'draft',
      start_date: body.start_date ?? null, expires_on: body.expires_on ?? null, next_billing_date: null,
      notes: body.notes ?? '', lines: linesFromTemplate(tpl), created_on: iso(0),
    }
    db.subscriptions.push(sub)
    return sub
  }

  const sub = db.subscriptions.find((s) => s.id === Number(id))
  if (!sub || (user.role === 'customer' && sub.customer.id !== user.id)) fail(404, 'not_found', 'Subscription not found.')
  if (!action) return sub

  requireStaff(user)
  const t = TRANSITIONS[action]
  if (!t) fail(404, 'not_found', 'Unknown action.')
  if (!t.from.includes(sub.status)) fail(409, 'invalid_transition', `Cannot ${action} a subscription that is ${sub.status}.`)
  const plan = db.plans.find((p) => p.id === sub.plan.id)
  if (action === 'pause' && !plan.is_pausable) planBlock('pausing')
  if (action === 'close' && !plan.is_closable) planBlock('closing')
  if (action === 'renew') {
    if (!plan.is_renewable) planBlock('renewal')
    if (!sub.expires_on) fail(409, 'no_expiry_date', 'This subscription has no expiry date to renew.')
    sub.expires_on = addPeriod(sub.expires_on, sub.plan.billing_period)
  }
  if (action === 'activate') {
    if (sub.expires_on && sub.expires_on < iso(0)) fail(409, 'subscription_expired', 'This subscription has already expired.')
    sub.start_date = sub.start_date || iso(0)
    sub.next_billing_date = addPeriod(iso(0), sub.plan.billing_period)
  }
  if (action === 'resume') sub.next_billing_date = addPeriod(sub.next_billing_date || iso(0), sub.plan.billing_period)
  sub.status = t.to
  return sub
}

/* ---------- invoices & payments ---------- */
function viewInvoice(inv) {
  const { sub, tax, total, paid } = invoiceTotals(inv)
  return {
    ...inv, subtotal: toM(sub), tax_total: toM(tax), discount_total: toM(inv.discount_c),
    total: toM(total), amount_paid: toM(paid), balance: toM(total - paid),
    is_overdue: inv.status === 'confirmed' && inv.due_date < iso(0),
    payments: db.payments.filter((p) => p.invoice_id === inv.id),
  }
}

function invoices(user, method, id, action, body = {}, params = {}) {
  if (!id) {
    let items = [...db.invoices].sort((a, b) => b.id - a.id)
    if (user.role === 'customer') items = items.filter((i) => i.customer_snapshot.customer_id === user.id && i.status !== 'draft')
    if (params.status) items = items.filter((i) => i.status === params.status)
    if (params.customer_id) items = items.filter((i) => i.customer_snapshot.customer_id === Number(params.customer_id))
    if (params.date_from) items = items.filter((i) => i.issue_date >= params.date_from)
    if (params.date_to) items = items.filter((i) => i.issue_date <= params.date_to)
    let views = items.map(viewInvoice)
    if (params.overdue === 'true') views = views.filter((v) => v.is_overdue)
    return paginate(views, params)
  }
  const inv = db.invoices.find((i) => i.id === Number(id))
  if (!inv || (user.role === 'customer' && (inv.customer_snapshot.customer_id !== user.id || inv.status === 'draft'))) fail(404, 'not_found', 'Invoice not found.')
  if (!action) return viewInvoice(inv)
  if (action === 'payments' && method === 'GET') return db.payments.filter((p) => p.invoice_id === inv.id)

  requireStaff(user)
  const { total, paid } = invoiceTotals(inv)
  const bad = () => fail(409, 'invalid_transition', `Cannot ${action} an invoice that is ${inv.status}.`)
  if (action === 'confirm') {
    if (inv.status !== 'draft') bad()
    inv.status = total === 0 ? 'paid' : 'confirmed'
  } else if (action === 'cancel') {
    if (!['draft', 'confirmed'].includes(inv.status)) bad()
    if (paid > 0) fail(409, 'invoice_has_payments', 'This invoice has payments and cannot be cancelled.')
    inv.status = 'cancelled'
  } else if (action === 'send') {
    if (!['confirmed', 'paid'].includes(inv.status)) fail(409, 'invoice_not_sendable', 'Only confirmed or paid invoices can be sent.')
  } else if (action === 'payments') {
    const fields = {}
    const amount = String(body.amount ?? '')
    if (!['cash', 'card', 'bank_transfer', 'upi', 'other'].includes(body.method)) fields.method = ['Choose a payment method.']
    if (!/^\d+(\.\d{1,2})?$/.test(amount) || toC(amount) <= 0) fields.amount = ['Enter an amount above zero with at most 2 decimals.']
    const date = body.payment_date || iso(0)
    if (date > iso(0)) fields.payment_date = ['Payment date cannot be in the future.']
    if (Object.keys(fields).length) invalid(fields)
    if (inv.status !== 'confirmed') fail(409, 'invoice_not_payable', 'Only confirmed invoices can take payments.')
    if (toC(amount) > total - paid) fail(409, 'overpayment', 'The amount is more than the balance due.')
    const p = { id: nextId(db.payments), invoice_id: inv.id, invoice_number: inv.number, method: body.method, amount: toM(toC(amount)), payment_date: date, note: body.note || '' }
    db.payments.push(p)
    if (invoiceTotals(inv).paid >= total) inv.status = 'paid'
    return p
  } else fail(404, 'not_found', 'Unknown action.')
  return viewInvoice(inv)
}

function billingRun(user) {
  requireAdmin(user)
  let created = 0
  db.subscriptions
    .filter((s) => s.status === 'active' && s.next_billing_date && s.next_billing_date <= iso(0))
    .forEach((s) => {
      db.invoices.push(mkInvoice(nextId(db.invoices), s, 'draft', 0, 15))
      s.next_billing_date = addPeriod(s.next_billing_date, s.plan.billing_period)
      created += 1
    })
  return { invoices_created: created, duplicates_skipped: 0, subscriptions_closed: 0, failures: 0 }
}

/* ---------- templates, customers, staff ---------- */
const viewTemplate = (t) => {
  const p = db.plans.find((x) => x.id === t.plan_id)
  return { ...t, plan: p ? { id: p.id, name: p.name } : null }
}

function templateFromBody(body, id) {
  const fields = {}
  const plan = db.plans.find((p) => p.id === body.plan_id)
  if (!body.name?.trim()) fields.name = ['Name is required.']
  if (!plan) fields.plan_id = ['Choose a plan.']
  if (!body.lines?.length) fields.lines = ['Add at least one line.']
  else {
    const bad = {}
    body.lines.forEach((l, i) => {
      const product = db.products.find((p) => p.id === l.product_id)
      const e = {}
      if (!product) e.product_id = ['Choose a product.']
      else if (l.variant_id != null && !product.variants.some((v) => v.id === l.variant_id)) e.variant_id = ['This variant belongs to a different product.']
      if (plan && !(l.quantity >= plan.min_quantity)) e.quantity = [`Minimum quantity is ${plan.min_quantity}.`]
      if (Object.keys(e).length) bad[i] = e
    })
    if (Object.keys(bad).length) fields.lines = bad
  }
  if (Object.keys(fields).length) invalid(fields)
  const lines = body.lines.map((l, i) => {
    const product = db.products.find((p) => p.id === l.product_id)
    const variant = product.variants.find((v) => v.id === l.variant_id)
    return tplLine(i + 1, product, variant, db.taxes.find((t) => t.id === l.tax_id), l.quantity)
  })
  return { id, name: body.name.trim(), plan_id: plan.id, validity_days: body.validity_days || 30, is_active: true, lines }
}

function templates(user, method, id, body = {}, params = {}) {
  requireStaff(user)
  if (!id) {
    if (method === 'GET') {
      const items = db.templates.filter((t) => params.include_inactive === 'true' || t.is_active)
      return paginate(items.map(viewTemplate), params)
    }
    requireAdmin(user)
    const t = templateFromBody(body, nextId(db.templates))
    db.templates.push(t)
    return viewTemplate(t)
  }
  const idx = db.templates.findIndex((t) => t.id === Number(id))
  if (idx < 0) fail(404, 'not_found', 'Template not found.')
  if (method === 'GET') return viewTemplate(db.templates[idx])
  requireAdmin(user)
  if (method === 'PUT') {
    db.templates[idx] = { ...templateFromBody(body, db.templates[idx].id), is_active: db.templates[idx].is_active }
    return viewTemplate(db.templates[idx])
  }
  db.templates[idx].is_active = false
  return viewTemplate(db.templates[idx])
}

function customers(user, method, id, body = {}, params = {}) {
  requireStaff(user)
  if (!id) {
    if (method === 'GET') {
      const q = (params.q || '').toLowerCase()
      const items = db.customers.filter((c) => !q || c.full_name.toLowerCase().includes(q) || c.email.includes(q))
      return paginate(items, params)
    }
    if (!body.full_name?.trim()) invalid({ full_name: ['Name is required.'] })
    if (db.customers.some((c) => c.email === body.email)) fail(409, 'email_taken', 'This email is already registered.', { email: ['This email is already registered.'] })
    const c = { id: Math.max(nextId(db.users), nextId(db.customers)), full_name: body.full_name.trim(), email: body.email, phone: body.phone || '', created_on: iso(0) }
    db.customers.push(c)
    return c
  }
  const c = db.customers.find((x) => x.id === Number(id))
  if (!c) fail(404, 'not_found', 'Customer not found.')
  if (method === 'PUT') Object.assign(c, { full_name: body.full_name, phone: body.phone })
  return c
}

function staff(user, method, body = {}, params = {}) {
  requireAdmin(user)
  if (method === 'GET') return paginate(db.users.filter((u) => u.role !== 'customer').map(publicUser), params)
  if (db.users.some((u) => u.email === body.email)) fail(409, 'email_taken', 'This email is already registered.', { email: ['This email is already registered.'] })
  const u = { id: Math.max(nextId(db.users), nextId(db.customers)), email: body.email, password: body.password, full_name: body.full_name, role: 'staff', staff_function: body.staff_function }
  db.users.push(u)
  return publicUser(u)
}

/* ---------- catalog (mock only until the backend has it) ---------- */
function catalog(user, method, res, id, body = {}, params = {}) {
  requireStaff(user)
  const list = db[res]
  if (!id) {
    if (method === 'GET') {
      const q = (params.q || '').toLowerCase()
      return paginate(list.filter((x) => !q || (x.name || '').toLowerCase().includes(q)), params)
    }
    requireAdmin(user)
    if (!body.name?.trim()) invalid({ name: ['Name is required.'] })
    if (res === 'discounts' && list.some((d) => d.code === body.code)) fail(409, 'name_taken', 'This discount code already exists.', { code: ['This discount code already exists.'] })
    const item = { is_active: true, ...body, name: body.name.trim(), id: nextId(list) }
    if (res === 'discounts') item.usage_count = 0
    if (res === 'products') item.variants = item.variants || []
    list.push(item)
    return item
  }
  const item = list.find((x) => x.id === Number(id))
  if (!item) fail(404, 'not_found', 'Not found.')
  if (method === 'GET') return item
  requireAdmin(user)
  if (method === 'PUT') {
    if (!body.name?.trim()) invalid({ name: ['Name is required.'] })
    const { id: _ignore, usage_count: _uc, ...rest } = body // eslint-disable-line no-unused-vars
    return Object.assign(item, rest)
  }
  item.is_active = false
  return item
}

/* ---------- reports ---------- */
function reports(user, which, params = {}) {
  requireStaff(user)
  const inRange = (d) => (!params.date_from || d >= params.date_from) && (!params.date_to || d <= params.date_to)
  const views = db.invoices.map(viewInvoice)
  if (which === 'summary') {
    const active = db.subscriptions.filter((s) => s.status === 'active')
    const factor = { daily: 30, weekly: 52 / 12, monthly: 1, yearly: 1 / 12 }
    const mrr = active.reduce((a, s) => a + s.lines.reduce((x, l) => x + toC(l.amount), 0) * factor[s.plan.billing_period], 0)
    const collected = db.payments.filter((p) => inRange(p.payment_date)).reduce((a, p) => a + toC(p.amount), 0)
    const outstanding = views.filter((v) => v.status === 'confirmed').reduce((a, v) => a + toC(v.balance), 0)
    return { active_subscriptions: active.length, mrr: toM(Math.round(mrr)), revenue_collected: toM(collected), outstanding: toM(outstanding), overdue_count: views.filter((v) => v.is_overdue).length }
  }
  if (which === 'revenue') {
    return Array.from({ length: 6 }, (_, i) => {
      const d = new Date()
      d.setDate(1)
      d.setMonth(d.getMonth() - (5 - i))
      const period = isoOf(d).slice(0, 7)
      const invoiced = views.filter((v) => ['confirmed', 'paid'].includes(v.status) && v.issue_date.startsWith(period)).reduce((a, v) => a + toC(v.total), 0)
      const collected = db.payments.filter((p) => p.payment_date.startsWith(period)).reduce((a, p) => a + toC(p.amount), 0)
      return { period, invoiced: toM(invoiced), collected: toM(collected) }
    })
  }
  const today = new Date(iso(0))
  const items = views.filter((v) => v.is_overdue).map((v) => ({ ...v, days_overdue: Math.round((today - new Date(v.due_date)) / 86400000) }))
  return paginate(items.sort((a, b) => b.days_overdue - a.days_overdue), params)
}

/* ---------- entry point ---------- */
export async function mockRequest(path, { method = 'GET', body, params = {} } = {}) {
  await delay()
  const [res, a, b] = path.split('/').filter(Boolean)
  if (res === 'auth') return auth(method, a, body)
  const user = current()
  if (!user) fail(401, 'unauthorized', 'Not logged in.')
  switch (res) {
    case 'subscriptions': return subscriptions(user, method, a, b, body, params)
    case 'invoices': return invoices(user, method, a, b, body, params)
    case 'payments': requireStaff(user); return paginate([...db.payments].reverse(), params)
    case 'billing': return billingRun(user)
    case 'quotation-templates': return templates(user, method, a, body, params)
    case 'customers': return customers(user, method, a, body, params)
    case 'staff': return staff(user, method, body, params)
    case 'reports': return reports(user, a, params)
    case 'products': case 'plans': case 'taxes': case 'discounts':
      return catalog(user, method, res, a, body, params)
    default: return fail(404, 'not_found', 'Not found.')
  }
}