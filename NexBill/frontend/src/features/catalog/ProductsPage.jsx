import { useFieldArray } from 'react-hook-form'
import Button from '../../components/Button'
import { FormField, Input } from '../../components/FormField'
import Icon from '../../components/Icon'
import ResourcePage from '../../components/ResourcePage'
import { productsApi } from '../../api/catalog'
import { formatMoney } from '../../utils/format'

function VariantFields({ control, register, formState: { errors } }) {
  const { fields, append, remove } = useFieldArray({ control, name: 'variants' })
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-slate-700">Variants</span>
        <Button variant="ghost" onClick={() => append({ attribute: '', value: '', extra_price: '' })}>+ Add variant</Button>
      </div>
      {typeof errors.variants?.message === 'string' && <p className="text-xs text-rose-600" role="alert">{errors.variants.message}</p>}
      {fields.map((field, index) => (
        <div key={field.id} className="grid grid-cols-[1fr_1fr_1fr_auto] items-start gap-2">
          <FormField error={errors.variants?.[index]?.attribute?.message}>
            <Input aria-label="Attribute" placeholder="Brand" {...register(`variants.${index}.attribute`)} />
          </FormField>
          <FormField error={errors.variants?.[index]?.value?.message}>
            <Input aria-label="Value" placeholder="Odoo" {...register(`variants.${index}.value`)} />
          </FormField>
          <FormField error={errors.variants?.[index]?.extra_price?.message}>
            <Input aria-label="Extra price" inputMode="decimal" placeholder="560.00" {...register(`variants.${index}.extra_price`)} />
          </FormField>
          <Button variant="ghost" className="w-9 !px-0" aria-label="Remove variant" onClick={() => remove(index)}><Icon name="x" /></Button>
        </div>
      ))}
    </div>
  )
}

const cleanVariants = (body, values) => ({
  ...body,
  variants: (values.variants ?? []).map(({ attribute, value, extra_price }) => ({
    attribute,
    value,
    ...(extra_price === '' ? {} : { extra_price }),
  })),
})

export default function ProductsPage() {
  return (
    <ResourcePage title="Products" subtitle="What you sell, with optional priced variants" noun="product" queryKey={['products']} api={productsApi}
      getRowLabel={(r) => r.name}
      defaults={{ variants: [], product_type: 'service' }}
      transform={cleanVariants}
      renderExtra={(form) => <VariantFields {...form} />}
      columns={[
        { key: 'name', header: 'Name' },
        { key: 'product_type', header: 'Type', className: 'capitalize' },
        { key: 'sales_price', header: 'Price', render: (r) => formatMoney(r.sales_price) },
        { key: 'variants', header: 'Variants', render: (r) => r.variants.map((v) => `${v.value} (+${formatMoney(v.extra_price)})`).join(', ') || '—' },
      ]}
      fields={[
        { name: 'name', label: 'Name' },
        { name: 'product_type', label: 'Type', type: 'select', options: [{ value: 'service', label: 'Service' }, { value: 'goods', label: 'Goods' }] },
        { name: 'sales_price', label: 'Sales price', type: 'money' },
        { name: 'cost_price', label: 'Cost price', type: 'money', hint: 'Optional' },
        { name: 'description', label: 'Description' },
      ]} />
  )
}
