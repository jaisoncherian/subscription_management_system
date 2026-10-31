export const SUB_STATUSES = ['draft', 'quotation', 'confirmed', 'active', 'paused', 'closed']

// How to display each action. Which ones apply comes from the API's allowed_actions.
export const SUB_ACTIONS = {
  'send-quotation': { action: 'send-quotation', label: 'Send quotation', variant: 'primary' },
  confirm: { action: 'confirm', label: 'Confirm', variant: 'primary' },
  activate: { action: 'activate', label: 'Activate', variant: 'primary' },
  pause: { action: 'pause', label: 'Pause', variant: 'secondary' },
  resume: { action: 'resume', label: 'Resume', variant: 'primary' },
  renew: { action: 'renew', label: 'Renew', variant: 'secondary', confirm: { title: 'Renew subscription?', message: 'This extends the expiry date by one billing period. The status stays Active.' } },
  close: { action: 'close', label: 'Close', variant: 'danger', confirm: { title: 'Close subscription?', message: 'A closed subscription cannot be reopened.', danger: true } },
}
