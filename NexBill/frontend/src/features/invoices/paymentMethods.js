export const PAYMENT_METHODS = [
  { value: 'card', label: 'Card' },
  { value: 'bank_transfer', label: 'Bank transfer' },
  { value: 'upi', label: 'UPI' },
  { value: 'cash', label: 'Cash' },
  { value: 'other', label: 'Other' },
]

export const paymentMethodLabel = (value) => PAYMENT_METHODS.find((m) => m.value === value)?.label ?? value
