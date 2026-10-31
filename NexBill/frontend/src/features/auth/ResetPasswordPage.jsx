import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout from '../../components/AuthLayout'
import Button from '../../components/Button'
import { FormField, Input } from '../../components/FormField'
import PasswordRules from '../../components/PasswordRules'
import { useToast } from '../../components/Toast'
import { authApi } from '../../api/auth'
import { resetSchema } from '../../schemas/auth'
import { applyServerError } from '../../utils/formErrors'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const navigate = useNavigate()
  const toast = useToast()
  const [badLink, setBadLink] = useState(!token)
  const { register, handleSubmit, setError, watch, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(resetSchema) })

  const onSubmit = async ({ password }) => {
    try {
      await authApi.resetPassword({ token, password })
      toast.success('Password updated. Please sign in.')
      navigate('/login', { replace: true })
    } catch (err) {
      if (err.code === 'invalid_reset_token') setBadLink(true)
      else applyServerError(err, setError, toast)
    }
  }

  if (badLink) {
    return (
      <AuthLayout title="Link not valid" subtitle="This reset link is invalid, expired or already used.">
        <Link to="/forgot-password"><Button className="w-full">Request a new link</Button></Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Set a new password" footer={<Link to="/login" className="font-medium text-brand-600 hover:underline">Back to sign in</Link>}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="New password" htmlFor="password" error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="new-password" invalid={errors.password} {...register('password')} />
        </FormField>
        <PasswordRules value={watch('password')} />
        <FormField label="Confirm password" htmlFor="confirm" error={errors.confirm?.message}>
          <Input id="confirm" type="password" autoComplete="new-password" invalid={errors.confirm} {...register('confirm')} />
        </FormField>
        <Button type="submit" loading={isSubmitting} className="w-full">Update password</Button>
      </form>
    </AuthLayout>
  )
}