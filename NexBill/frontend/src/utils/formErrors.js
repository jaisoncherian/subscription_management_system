export function applyServerError(err, setError, toast) {
  if (err?.status === 429) {
    toast.error('Too many attempts. Please try again shortly.')
    return
  }
  let mapped = false
  Object.entries(err?.fields || {}).forEach(([name, msgs]) => {
    if (Array.isArray(msgs)) {
      setError(name, { type: 'server', message: msgs.join(' ') })
      mapped = true
    }
  })
  if (!mapped) toast.error(err?.message || 'Something went wrong.')
}