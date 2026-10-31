import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../features/auth/AuthContext'
import { applyServerError } from '../utils/formErrors'
import Button from './Button'
import ConfirmDialog from './ConfirmDialog'
import { FormField, Input, Select } from './FormField'
import ListPage from './ListPage'
import Modal from './Modal'
import StatusBadge from './StatusBadge'
import { useToast } from './Toast'

function Field({ field, register, errors }) {
  const error = errors[field.name]?.message
  const id = `field-${field.name}`
  if (field.type === 'checkbox') {
    return (
      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" {...register(field.name)} /> {field.label}
      </label>
    )
  }
  return (
    <FormField label={field.label} htmlFor={id} error={error} hint={field.hint}>
      {field.type === 'select' ? (
        <Select id={id} invalid={error} defaultValue="" {...register(field.name)}>
          <option value="" disabled>Select…</option>
          {field.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </Select>
      ) : (
        <Input id={id} invalid={error} type={field.type === 'money' ? 'text' : field.type ?? 'text'}
          inputMode={field.type === 'money' ? 'decimal' : undefined} autoComplete={field.type === 'password' ? 'new-password' : 'off'}
          {...register(field.name)} />
      )}
    </FormField>
  )
}

// Empty inputs are left out, so the API applies its defaults.
function toBody(fields, values) {
  const body = {}
  fields.forEach(({ name, type }) => {
    const value = values[name]
    if (value === '' || value == null) return
    body[name] = type === 'number' || type === 'id' || (type === 'select' && /^\d+$/.test(value)) ? Number(value) : value
  })
  return body
}

function ResourceForm({ title, fields, defaults, renderExtra, transform, create, onDone, successMessage }) {
  const toast = useToast()
  const form = useForm({ defaultValues: defaults })
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = form

  const onSubmit = async (values) => {
    const body = toBody(fields, values)
    try {
      await create(transform ? transform(body, values) : body)
      toast.success(successMessage)
      onDone()
    } catch (err) {
      applyServerError(err, setError, toast)
    }
  }

  return (
    <Modal open onClose={onDone} title={title}
      footer={<>
        <Button variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" form="resource-form" loading={isSubmitting}>Save</Button>
      </>}>
      <form id="resource-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {fields.map((f) => <Field key={f.name} field={f} register={register} errors={errors} />)}
        {renderExtra?.(form)}
      </form>
    </Modal>
  )
}

// A list with an "Add" form and a "Deactivate" action, for the catalog-style screens.
// Every validation rule lives in the API. Its field errors appear next to the inputs.
export default function ResourcePage({ title, subtitle, noun, queryKey, api, columns, fields, defaults, renderExtra, transform, getRowLabel }) {
  const { user } = useAuth()
  const toast = useToast()
  const qc = useQueryClient()
  const [adding, setAdding] = useState(false)
  const [target, setTarget] = useState(null)
  const isAdmin = user.role === 'admin'

  const refresh = () => qc.invalidateQueries({ queryKey })
  const create = useMutation({ mutationFn: api.create, onSuccess: refresh })
  const deactivate = useMutation({ mutationFn: (row) => api.deactivate(row.id), onSuccess: refresh })

  const confirmDeactivate = async () => {
    try {
      await deactivate.mutateAsync(target)
      toast.success(`${getRowLabel(target)} deactivated`)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setTarget(null)
    }
  }

  const allColumns = [
    ...columns,
    ...(api.deactivate ? [
      { key: 'is_active', header: 'Status', render: (r) => <StatusBadge status={r.is_active ? 'active' : 'closed'} /> },
    ] : []),
    ...(api.deactivate && isAdmin ? [{
      key: 'actions', header: '', className: 'text-right',
      render: (r) => r.is_active && <Button variant="ghost" onClick={() => setTarget(r)}>Deactivate</Button>,
    }] : []),
  ]

  return (
    <>
      <ListPage title={title} subtitle={subtitle} queryKey={queryKey} fetchPage={api.list} columns={allColumns}
        actions={isAdmin && <Button onClick={() => setAdding(true)}>+ New {noun}</Button>} />
      {adding && (
        <ResourceForm title={`New ${noun}`} fields={fields} defaults={defaults} renderExtra={renderExtra} transform={transform}
          create={create.mutateAsync} onDone={() => setAdding(false)} successMessage={`${noun[0].toUpperCase()}${noun.slice(1)} created`} />
      )}
      <ConfirmDialog open={!!target} title={`Deactivate ${noun}?`} danger confirmLabel="Deactivate" loading={deactivate.isPending}
        message="It can no longer be used for anything new. Existing subscriptions and invoices keep it."
        onConfirm={confirmDeactivate} onCancel={() => setTarget(null)} />
    </>
  )
}
