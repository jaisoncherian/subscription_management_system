export const SUB_STATUSES = ['draft', 'quotation', 'confirmed', 'active', 'paused', 'closed']

// How to display each action. Which ones apply comes from the API's allowed_actions.
export const SUB_ACTIONS = {
  'send-quotation': { action: 'send-quotation', label: 'Send quotation', done: 'Quotation sent', variant: 'primary' },
  confirm: { action: 'confirm', label: 'Confirm', done: 'Subscription confirmed', variant: 'primary' },
  activate: { action: 'activate', label: 'Activate', done: 'Subscription activated', variant: 'primary' },
  pause: { action: 'pause', label: 'Pause', done: 'Subscription paused', variant: 'secondary' },
  resume: { action: 'resume', label: 'Resume', done: 'Subscription resumed', variant: 'primary' },
  renew: { action: 'renew', label: 'Renew', done: 'Subscription renewed', variant: 'secondary', confirm: { title: 'Renew subscription?', message: 'This extends the expiry date by one billing period. The status stays Active.' } },
  close: { action: 'close', label: 'Close', done: 'Subscription closed', variant: 'danger', confirm: { title: 'Close subscription?', message: 'A closed subscription cannot be reopened.', danger: true } },
}
