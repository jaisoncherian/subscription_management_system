import { z } from 'zod'

export const passwordRules = [
  { key: 'length', label: 'More than 8 characters', test: (p) => p.length > 8 && p.length <= 128 },
  { key: 'upper', label: 'An uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { key: 'lower', label: 'A lowercase letter', test: (p) => /[a-z]/.test(p) },
  { key: 'special', label: 'A special character (a space does not count)', test: (p) => /[^A-Za-z0-9\s]/.test(p) },
]

const email = z.string().trim().toLowerCase().email('Enter a valid email address')
const password = z.string().refine((p) => passwordRules.every((r) => r.test(p)), 'Password does not meet all the rules')

export const loginSchema = z.object({ email, password: z.string().min(1, 'Password is required') })

export const signupSchema = z
  .object({ full_name: z.string().trim().min(2, 'Enter your full name'), email, password, confirm: z.string() })
  .refine((d) => d.password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] })

export const forgotSchema = z.object({ email })

export const resetSchema = z
  .object({ password, confirm: z.string() })
  .refine((d) => d.password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] })