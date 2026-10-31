import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import AuthLayout from '../../components/AuthLayout'
import Button from '../../components/Button'
import { FormField, Input } from '../../components/FormField'
import PasswordRules from '../../components/PasswordRules'
import { useToast } from '../../components/Toast'
import { authApi } from '../../api/auth'
import { signupSchema } from '../../schemas/auth'
import { applyServerError } from '../../utils/formErrors'

export default function SignupPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const { register, handleSubmit, setError, watch, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(signupSchema) })

  const onSubmit = async ({ full_name, email, password }) => {
    try {
      await authApi.register({ full_name, email, password })
      toast.success('Account created. Please sign in.')
      navigate('/login', { replace: true })
    } catch (err) {
      applyServerError(err, setError, toast)
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Sign up as a customer"
      footer={<>Already have an account? <Link to="/login" className="font-medium text-brand-600 hover:underline">Sign in</Link></>}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
          <Input id="full_name" autoComplete="name" invalid={errors.full_name} {...register('full_name')} />
        </FormField>
        <FormField label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" invalid={errors.email} {...register('email')} />
        </FormField>
        <FormField label="Password" htmlFor="password" error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="new-password" invalid={errors.password} {...register('password')} />
        </FormField>
        <PasswordRules value={watch('password')} />
        <FormField label="Confirm password" htmlFor="confirm" error={errors.confirm?.message}>
          <Input id="confirm" type="password" autoComplete="new-password" invalid={errors.confirm} {...register('confirm')} />
        </FormField>
        <Button type="submit" loading={isSubmitting} className="w-full">Create account</Button>
      </form>
    </AuthLayout>
  )
}