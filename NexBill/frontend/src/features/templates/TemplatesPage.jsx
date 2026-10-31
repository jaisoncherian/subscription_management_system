import { useFieldArray } from 'react-hook-form'
import { useQuery } from '@tanstack/react-query'
import Button from '../../components/Button'
import { FormField, Input, Select } from '../../components/FormField'
import ResourcePage from '../../components/ResourcePage'
import { plansApi, productsApi, taxesApi } from '../../api/catalog'
import { templatesApi } from '../../api/templates'
import { useAuth } from '../auth/AuthContext'

const useActive = (key, api, enabled) => {
  const { data } = useQuery({ queryKey: [key, 'all'], queryFn: () => api.list({ page_size: 100 }), enabled })
  return (data?.items ?? []).filter((item) => item.is_active)
}

function LineFields({ control, register, watch, formState: { errors }, products, taxes }) {
  const { fields, append, remove } = useFieldArray({ control, name: 'lines' })
  const lines = watch('lines')
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">Lines</span>
        <Button variant="ghost" onClick={() => append({ product_id: '', variant_id: '', tax_id: '', quantity: 1 })}>+ Add line</Button>
      </div>
      {typeof errors.lines?.message === 'string' && <p className="text-xs text-rose-600" role="alert">{errors.lines.message}</p>}
      {fields.map((field, index) => {
        const lineErrors = errors.lines?.[index]
        const product = products.find((p) => p.id === Number(lines?.[index]?.product_id))
        const variants = (product?.variants ?? []).filter((v) => v.is_active)
        return (
          <div key={field.id} className="space-y-2 rounded-lg border border-slate-200 p-3">
            <FormField error={lineErrors?.product_id?.message}>
              <Select aria-label="Product" {...register(`lines.${index}.product_id`)}>
                <option value="">Select a product…</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </Select>
            </FormField>
            <div className="grid grid-cols-[1fr_1fr_5rem_auto] items-start gap-2">
              <FormField error={lineErrors?.variant_id?.message}>
                <Select aria-label="Variant" {...register(`lines.${index}.variant_id`)}>
                  <option value="">No variant</option>
                  {variants.map((v) => <option key={v.id} value={v.id}>{v.attribute}: {v.value}</option>)}
                </Select>
              </FormField>
              <FormField error={lineErrors?.tax_id?.message}>
                <Select aria-label="Tax" {...register(`lines.${index}.tax_id`)}>
                  <option value="">No tax</option>
                  {taxes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </Select>
              </FormField>
              <FormField error={lineErrors?.quantity?.message}>
                <Input aria-label="Quantity" type="number" min="1" {...register(`lines.${index}.quantity`)} />
              </FormField>
              <Button variant="ghost" aria-label="Remove line" onClick={() => remove(index)}>✕</Button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

const number = (value) => (value === '' || value == null ? undefined : Number(value))
const toLines = (body, values) => ({
  ...body,
  lines: (values.lines ?? []).map((l) => ({
    // An unchosen product is sent as null, so the API reports it next to that line.
    product_id: number(l.product_id) ?? null,
    variant_id: number(l.variant_id) ?? null,
    tax_id: number(l.tax_id) ?? null,
    quantity: number(l.quantity) ?? 1,
  })),
})

export default function TemplatesPage() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const plans = useActive('plans', plansApi, isAdmin)
  const products = useActive('products', productsApi, isAdmin)
  const taxes = useActive('taxes', taxesApi, isAdmin)

  return (
    <ResourcePage title="Quotation templates" subtitle="Reusable plan and lines for new subscriptions" noun="template" queryKey={['templates']}
      api={templatesApi} getRowLabel={(r) => r.name}
      defaults={{ validity_days: 30, lines: [{ product_id: '', variant_id: '', tax_id: '', quantity: 1 }] }}
      transform={toLines}
      renderExtra={(form) => <LineFields {...form} products={products} taxes={taxes} />}
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'plan_name', header: 'Plan' },
        { key: 'validity_days', header: 'Valid for', render: (r) => `${r.validity_days} days` },
        { key: 'lines', header: 'Products', render: (r) => r.lines.map((l) => `${l.product_name} × ${l.quantity}`).join(', ') },
      ]}
      fields={[
        { name: 'name', label: 'Name' },
        { name: 'plan_id', label: 'Plan', type: 'select', options: plans.map((p) => ({ value: p.id, label: p.name })) },
        { name: 'validity_days', label: 'Quotation valid for (days)', type: 'number' },
      ]} />
  )
}
