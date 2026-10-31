import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import DataTable from './DataTable'
import PageHeader from './PageHeader'
import Pagination from './Pagination'

const PAGE_SIZE = 10

// A page of rows from any list endpoint, with loading, error and paging handled.
export default function ListPage({ title, subtitle, actions, queryKey, fetchPage, params = {}, columns, getRowKey, onRowClick, empty, children }) {
  const [page, setPage] = useState(1)
  const paramKey = JSON.stringify(params)
  const [lastKey, setLastKey] = useState(paramKey)
  if (paramKey !== lastKey) {
    setLastKey(paramKey)
    setPage(1)
  }
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: [...queryKey, { page, ...params }],
    queryFn: () => fetchPage({ page, page_size: PAGE_SIZE, ...params }),
    placeholderData: keepPreviousData,
  })

  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} actions={actions} />
      {children}
      {isError ? (
        <div role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
          {error.message} <button className="ml-2 underline" onClick={() => refetch()}>Retry</button>
        </div>
      ) : (
        <>
          <DataTable loading={isLoading} rows={data?.items} columns={columns} getRowKey={getRowKey} onRowClick={onRowClick} empty={empty} />
          <Pagination page={page} perPage={PAGE_SIZE} total={data?.total ?? 0} onPageChange={setPage} />
        </>
      )}
    </div>
  )
}
