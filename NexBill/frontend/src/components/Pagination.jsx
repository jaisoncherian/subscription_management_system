import Button from './Button'
import Icon from './Icon'

export default function Pagination({ page, perPage, total, onPageChange }) {
  const pages = Math.max(1, Math.ceil(total / perPage))
  const from = total === 0 ? 0 : (page - 1) * perPage + 1
  const to = Math.min(page * perPage, total)
  return (
    <div className="flex items-center justify-between gap-3 pt-4 text-[13px] text-slate-500">
      <span className="tabular-nums">{from}–{to} of {total}</span>
      <div className="flex items-center gap-2">
        <span className="tabular-nums">Page {page} of {pages}</span>
        <Button variant="secondary" className="w-9 !px-0" aria-label="Previous" disabled={page <= 1} onClick={() => onPageChange(page - 1)}><Icon name="chevronLeft" /></Button>
        <Button variant="secondary" className="w-9 !px-0" aria-label="Next" disabled={page >= pages} onClick={() => onPageChange(page + 1)}><Icon name="chevronRight" /></Button>
      </div>
    </div>
  )
}
