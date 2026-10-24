import type { ReactNode } from 'react'

export function DataTable({
  headers,
  rows,
  emptyMessage = 'Aucune donnée à afficher.',
}: {
  headers: string[]
  rows: ReactNode[][]
  emptyMessage?: string
}) {
  if (rows.length === 0) return <div className="table-empty">{emptyMessage}</div>
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
