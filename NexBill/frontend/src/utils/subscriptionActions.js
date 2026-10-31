export const SUB_STATUSES = ['draft', 'quotation', 'confirmed', 'active', 'paused', 'closed']

const close = { action: 'close', label: 'Close', variant: 'danger', confirm: { title: 'Close subscription?', message: 'A closed subscription cannot be reopened.', danger: true } }

export const SUB_ACTIONS = {
  draft: [{ action: 'send-quotation', label: 'Send quotation', variant: 'primary' }],
  quotation: [{ action: 'confirm', label: 'Confirm', variant: 'primary' }],
  confirmed: [{ action: 'activate', label: 'Activate', variant: 'primary' }],
  active: [
    { action: 'pause', label: 'Pause', variant: 'secondary' },
    { action: 'renew', label: 'Renew', variant: 'secondary', confirm: { title: 'Renew subscription?', message: 'This extends the expiry date by one billing period. The status stays Active.' } },
    close,
  ],
  paused: [{ action: 'resume', label: 'Resume', variant: 'primary' }, close],
  closed: [],
}