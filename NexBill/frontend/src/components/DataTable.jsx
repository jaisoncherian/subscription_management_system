import EmptyState from './EmptyState'

export default function DataTable({ columns, rows = [], loading = false, getRowKey = (r) => r.id, onRowClick, empty }) {
  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm tabular-nums">
          <thead>
            <tr className="border-b border-slate-200/80 bg-slate-50/70">
              {columns.map((c) => (
                <th key={c.key} scope="col" className={`eyebrow whitespace-nowrap px-5 py-3 text-left ${c.className ?? ''}`}>{c.header}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {columns.map((c) => (
                      <td key={c.key} className="px-5 py-3.5"><div className="h-4 w-3/4 animate-pulse rounded bg-slate-100" /></td>
                    ))}
                  </tr>
                ))
              : rows.map((row) => (
                  <tr key={getRowKey(row)}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    onKeyDown={onRowClick ? (e) => e.key === 'Enter' && onRowClick(row) : undefined}
                    tabIndex={onRowClick ? 0 : undefined}
                    className={`transition-colors ${onRowClick ? 'cursor-pointer hover:bg-brand-50/40 focus:bg-brand-50/40 focus:outline-none' : ''}`}>
                    {columns.map((c) => (
                      <td key={c.key} className={`px-5 py-3.5 text-slate-700 ${c.className ?? ''}`}>
                        {c.render ? c.render(row) ?? '—' : row[c.key] ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
      {!loading && rows.length === 0 && (empty ?? <EmptyState />)}
    </div>
  )
}
