const PAGE_SIZES = [10, 20, 50, 100] as const

function pageNumbers(currentPage: number, totalPages: number): (number | 'ellipsis-start' | 'ellipsis-end')[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }
  if (currentPage <= 4) {
    return [1, 2, 3, 4, 5, 'ellipsis-end', totalPages]
  }
  if (currentPage >= totalPages - 3) {
    return [1, 'ellipsis-start', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages]
  }
  return [1, 'ellipsis-start', currentPage - 1, currentPage, currentPage + 1, 'ellipsis-end', totalPages]
}

export function PaginationControls({
  page,
  pageSize,
  totalCount,
  totalPages,
  itemLabel,
  onPageChange,
  onPageSizeChange,
}: {
  page: number
  pageSize: number
  totalCount: number
  totalPages: number
  itemLabel: string
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}) {
  const start = totalCount === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, totalCount)
  const pages = pageNumbers(page, totalPages)

  return (
    <nav className="pagination-controls" aria-label={`Pagination des ${itemLabel}`}>
      <div className="pagination-summary" aria-live="polite">
        <label>
          {itemLabel} par page
          <select
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {PAGE_SIZES.map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </label>
        <span>
          Affichage de {start} à {end} sur {totalCount} {itemLabel}
        </span>
        <span>
          Page {totalPages === 0 ? 0 : page} sur {totalPages}
        </span>
      </div>
      <div className="pagination-buttons">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Précédent
        </button>
        {pages.map((pageNumber, index) =>
          typeof pageNumber === 'number' ? (
            <button
              type="button"
              key={pageNumber}
              className="pagination-number"
              aria-label={`Page ${pageNumber}`}
              aria-current={pageNumber === page ? 'page' : undefined}
              onClick={() => onPageChange(pageNumber)}
            >
              {pageNumber}
            </button>
          ) : (
            <span className="pagination-ellipsis" key={`${pageNumber}-${index}`} aria-hidden="true">
              …
            </span>
          ),
        )}
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={totalPages === 0 || page >= totalPages}
        >
          Suivant
        </button>
      </div>
    </nav>
  )
}
