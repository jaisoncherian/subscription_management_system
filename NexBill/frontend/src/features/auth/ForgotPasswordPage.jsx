import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import AuthLayout from '../../components/AuthLayout'
import Button from '../../components/Button'
import { FormField, Input } from '../../components/FormField'
import { useToast } from '../../components/Toast'
import { authApi } from '../../api/auth'
import { forgotSchema } from '../../schemas/auth'

export default function ForgotPasswordPage() {
  const toast = useToast()
  const [sent, setSent] = useState(false)
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(forgotSchema) })

  const onSubmit = async (values) => {
    try {
      await authApi.forgotPassword(values)
      setSent(true)
    } catch (err) {
      if (err.status === 429) toast.error('Too many attempts. Please try again shortly.')
      else setSent(true) // never reveal whether an account exists
    }
  }

  return (
    <AuthLayout title="Forgot password?" subtitle="We'll email you a reset link"
      footer={<Link to="/login" className="font-medium text-brand-600 hover:underline">Back to sign in</Link>}>
      {sent ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-relaxed text-emerald-800" role="status">
          If an account exists for that email, a reset link is on its way. The link works once and expires in 30 minutes.
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <FormField label="Email" htmlFor="email" error={errors.email?.message}>
            <Input id="email" type="email" invalid={errors.email} {...register('email')} />
          </FormField>
          <Button type="submit" loading={isSubmitting} className="w-full">Send reset link</Button>
        </form>
      )}
    </AuthLayout>
  )
}