export const CURRENCY_SYMBOL = '₹'

export function formatMoney(value) {
  if (value == null || value === '') return '—'
  const [int, dec = '00'] = String(value).split('.')
  const negative = int.startsWith('-')
  const whole = Number(int.replace('-', '')).toLocaleString('en-IN')
  return `${negative ? '-' : ''}${CURRENCY_SYMBOL}${whole}.${dec.padEnd(2, '0')}`
}

export function formatDate(value) {
  if (!value) return '—'
  const [y, m, d] = String(value).slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

export function todayISO() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}