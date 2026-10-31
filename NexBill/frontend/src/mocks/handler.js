import { ApiError } from '../api/client'

const delay = (ms = 250) => new Promise((r) => setTimeout(r, ms))
const KEY = 'mock_user_id'

const users = [
  { id: 1, email: 'admin@brightloop.com', password: 'Admin@12345', full_name: 'Asha Admin', role: 'admin', staff_function: null },
  { id: 2, email: 'staff@brightloop.com', password: 'Staff@12345', full_name: 'Sam Staff', role: 'staff', staff_function: 'sales_rep' },
  { id: 3, email: 'customer@brightloop.com', password: 'Customer@123', full_name: 'Cora Customer', role: 'customer', staff_function: null },
]

const publicUser = ({ password, ...u }) => u // eslint-disable-line no-unused-vars
const current = () => users.find((u) => u.id === Number(sessionStorage.getItem(KEY)))

function fail(status, code, message, fields = {}) {
  throw new ApiError({ code, message, fields }, status)
}

export async function mockRequest(path, { method = 'GET', body } = {}) {
  await delay()
  switch (`${method} ${path}`) {
    case 'POST /auth/login': {
      const u = users.find((x) => x.email === body.email && x.password === body.password)
      if (!u) fail(401, 'invalid_credentials', 'Invalid email or password.')
      sessionStorage.setItem(KEY, String(u.id))
      return publicUser(u)
    }
    case 'POST /auth/register': {
      if (users.some((x) => x.email === body.email)) {
        fail(409, 'email_taken', 'This email is already registered.', { email: ['This email is already registered.'] })
      }
      const u = { id: users.length + 1, email: body.email, password: body.password, full_name: body.full_name, role: 'customer', staff_function: null }
      users.push(u)
      return publicUser(u)
    }
    case 'POST /auth/logout':
      sessionStorage.removeItem(KEY)
      return { message: 'Logged out' }
    case 'GET /auth/me': {
      const u = current()
      if (!u) fail(401, 'unauthorized', 'Not logged in.')
      return publicUser(u)
    }
    case 'POST /auth/forgot-password':
      return { message: 'If that email exists, a reset link has been sent.' }
    case 'POST /auth/reset-password':
      if (body.token === 'expired') fail(400, 'invalid_reset_token', 'This reset link is invalid or has expired.')
      return { message: 'Password updated.' }
    default:
      if (!current()) fail(401, 'unauthorized', 'Not logged in.')
      fail(404, 'not_found', `Mock for ${method} ${path} is not built yet.`)
  }
}