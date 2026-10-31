import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import AuthLayout from '../../components/AuthLayout'
import Button from '../../components/Button'
import { FormField, Input } from '../../components/FormField'
import { useToast } from '../../components/Toast'
import { loginSchema } from '../../schemas/auth'
import { applyServerError } from '../../utils/formErrors'
import { useAuth, homeFor } from './AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const [loginError, setLoginError] = useState('')
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (values) => {
    setLoginError('')
    try {
      const u = await login(values)
      navigate(homeFor(u.role), { replace: true })
    } catch (err) {
      if (err.code === 'invalid_credentials') setLoginError('Invalid email or password.')
      else applyServerError(err, setError, toast)
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your account"
      footer={<>New here? <Link to="/signup" className="font-medium text-brand-600 hover:underline">Create an account</Link></>}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {loginError && <div role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{loginError}</div>}
        <FormField label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" invalid={errors.email} {...register('email')} />
        </FormField>
        <FormField label="Password" htmlFor="password" error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="current-password" invalid={errors.password} {...register('password')} />
        </FormField>
        <div className="text-right text-sm">
          <Link to="/forgot-password" className="text-brand-600 hover:underline">Forgot password?</Link>
        </div>
        <Button type="submit" loading={isSubmitting} className="w-full">Sign in</Button>
      </form>
      <div className="mt-6 rounded-lg bg-slate-100 p-3 text-xs text-slate-600">
        <p className="mb-1 font-medium">Demo logins (mock mode)</p>
        <p>admin@brightloop.com / Admin@12345</p>
        <p>staff@brightloop.com / Staff@12345</p>
        <p>customer@brightloop.com / Customer@123</p>
      </div>
    </AuthLayout>
  )
}