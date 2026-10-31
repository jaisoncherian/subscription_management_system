// Field errors can be nested, such as fields.lines["0"].quantity.
function setFieldErrors(fields, setError, prefix = '') {
  let mapped = false
  Object.entries(fields).forEach(([name, value]) => {
    const path = `${prefix}${name}`
    if (Array.isArray(value)) {
      setError(path, { type: 'server', message: value.join(' ') })
      mapped = true
    } else if (value && typeof value === 'object') {
      mapped = setFieldErrors(value, setError, `${path}.`) || mapped
    }
  })
  return mapped
}

export function applyServerError(err, setError, toast) {
  if (err?.status === 429) {
    toast.error('Too many attempts. Please try again shortly.')
    return
  }
  if (!setFieldErrors(err?.fields || {}, setError)) {
    toast.error(err?.message || 'Something went wrong.')
  }
}
