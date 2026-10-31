let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

function csrfToken() {
  const m = document.cookie.match(/(?:^|; )csrf_access_token=([^;]*)/)
  return m ? decodeURIComponent(m[1]) : null
}

export class ApiError extends Error {
  constructor({ code, message, fields }, status) {
    super(message)
    this.code = code
    this.fields = fields || {}
    this.status = status
  }
}

function toQuery(params) {
  if (!params) return ''
  const clean = Object.entries(params).filter(([, v]) => v !== '' && v != null)
  return clean.length ? `?${new URLSearchParams(clean)}` : ''
}

export async function api(path, { method = 'GET', body, params } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET' && csrfToken()) headers['X-CSRF-TOKEN'] = csrfToken()

  const response = await fetch(`/api${path}${toQuery(params)}`, {
    method,
    headers,
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (response.status === 204) return null
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const err = new ApiError(
      data?.error ?? { code: 'server_error', message: 'Something went wrong.' },
      response.status,
    )
    if (response.status === 401 && err.code !== 'invalid_credentials') onUnauthorized()
    throw err
  }
  return data
}