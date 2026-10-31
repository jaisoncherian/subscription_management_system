import { useQuery } from '@tanstack/react-query'
import { FormField, Select } from '../../components/FormField'
import ResourcePage from '../../components/ResourcePage'
import { discountsApi, productsApi } from '../../api/catalog'
import { formatDate, formatMoney } from '../../utils/format'

function ProductPicker({ register, watch, formState: { errors } }) {
  const { data } = useQuery({ queryKey: ['products', 'all'], queryFn: () => productsApi.list({ page_size: 100 }) })
  if (watch('scope') !== 'product') return null
  return (
    <FormField label="Applies to" htmlFor="product_ids" error={errors.product_ids?.message} hint="Hold Ctrl to pick more than one">
      <Select id="product_ids" multiple {...register('product_ids')}>
        {data?.items.filter((p) => p.is_active).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
      </Select>
    </FormField>
  )
}

const withProducts = (body, values) => ({
  ...body,
  product_ids: values.scope === 'product' ? (values.product_ids ?? []).map(Number) : [],
})

export default function DiscountsPage() {
  return (
    <ResourcePage title="Discounts" subtitle="Applied per invoice until the usage limit runs out" noun="discount" queryKey={['discounts']} api={discountsApi}
      getRowLabel={(r) => r.code}
      defaults={{ discount_type: 'percent', scope: 'subscription', product_ids: [] }}
      transform={withProducts}
      renderExtra={(form) => <ProductPicker {...form} />}
      columns={[
        { key: 'code', header: 'Code' },
        { key: 'name', header: 'Name' },
        { key: 'value', header: 'Value', render: (r) => (r.discount_type === 'percent' ? `${r.value}%` : formatMoney(r.value)) },
        { key: 'scope', header: 'Scope', className: 'capitalize' },
        { key: 'usage', header: 'Used', render: (r) => `${r.usage_count}${r.usage_limit == null ? '' : ` / ${r.usage_limit}`}` },
        { key: 'valid_to', header: 'Valid to', render: (r) => formatDate(r.valid_to) },
      ]}
      fields={[
        { name: 'code', label: 'Code' },
        { name: 'name', label: 'Name' },
        { name: 'discount_type', label: 'Type', type: 'select', options: [{ value: 'percent', label: 'Percent' }, { value: 'fixed', label: 'Fixed amount' }] },
        { name: 'value', label: 'Value', type: 'money' },
        { name: 'scope', label: 'Applies to', type: 'select', options: [{ value: 'subscription', label: 'Whole subscription' }, { value: 'product', label: 'Specific products' }] },
        { name: 'usage_limit', label: 'Usage limit', type: 'number', hint: 'Empty means unlimited' },
        { name: 'min_purchase', label: 'Minimum purchase', type: 'money', hint: 'Optional' },
        { name: 'min_quantity', label: 'Minimum quantity', type: 'number', hint: 'Optional' },
        { name: 'valid_from', label: 'Valid from', type: 'date' },
        { name: 'valid_to', label: 'Valid to', type: 'date' },
      ]} />
  )
}
