import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface CategoryAggregate {
  category: string
  category_is_missing: boolean
  convention_count: number
  denominator: number
  percentage: number | null
}

function formatCount(value: number): string {
  return new Intl.NumberFormat('fr-FR').format(value)
}

function formatPercentage(value: number | null): string {
  if (value === null) return 'Non calculable'
  return `${new Intl.NumberFormat('fr-FR', {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(value)} %`
}

function EmptyChart({ message }: { message: string }) {
  return <div className="chart-empty">{message}</div>
}

export default function CategoryChart({
  title,
  data,
  color,
  horizontal = false,
  wide = false,
}: {
  title: string
  data: CategoryAggregate[]
  color: string
  horizontal?: boolean
  wide?: boolean
}) {
  const rows = horizontal
    ? [...data].sort((a, b) => a.convention_count - b.convention_count)
    : data
  const chartHeight = horizontal
    ? Math.max(220, rows.length * 48 + 35)
    : 290

  return (
    <article
      className={`chart-card${wide ? ' chart-card-full' : horizontal ? ' chart-card-wide' : ''}`}
    >
      <div className="chart-title-row">
        <div>
          <h2>{title}</h2>
          <p>
            Conventions distinctes · dénominateur :{' '}
            {formatCount(data[0]?.denominator ?? 0)}
          </p>
        </div>
      </div>
      {rows.length === 0 ? (
        <EmptyChart message="Aucune catégorie à afficher pour ce périmètre." />
      ) : (
        <div className="chart-canvas" style={{ height: chartHeight }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={rows}
              layout={horizontal ? 'vertical' : 'horizontal'}
              margin={
                horizontal
                  ? { top: 8, right: 22, bottom: 6, left: 12 }
                  : { top: 12, right: 10, bottom: 14, left: -12 }
              }
            >
              <CartesianGrid
                stroke="#e9edf2"
                strokeDasharray="3 4"
                vertical={!horizontal}
                horizontal={horizontal}
              />
              {horizontal ? (
                <>
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#728096', fontSize: 12 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="category"
                    width={135}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#516176', fontSize: 12 }}
                  />
                </>
              ) : (
                <>
                  <XAxis
                    dataKey="category"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#516176', fontSize: 12 }}
                    interval={0}
                    angle={rows.length > 5 ? -22 : 0}
                    textAnchor={rows.length > 5 ? 'end' : 'middle'}
                    height={rows.length > 5 ? 58 : 35}
                  />
                  <YAxis
                    allowDecimals={false}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#728096', fontSize: 12 }}
                    width={48}
                  />
                </>
              )}
              <Tooltip
                cursor={{ fill: '#f2f6f9' }}
                content={({ active, payload }) => {
                  const row = payload?.[0]?.payload as
                    | CategoryAggregate
                    | undefined
                  if (!active || !row) return null
                  return (
                    <div className="chart-tooltip">
                      <strong>{row.category}</strong>
                      <span>
                        {formatCount(row.convention_count)} convention(s)
                      </span>
                      <span>
                        {formatPercentage(row.percentage)} · dénominateur{' '}
                        {formatCount(row.denominator)}
                      </span>
                    </div>
                  )
                }}
              />
              <Bar
                dataKey="convention_count"
                name="Conventions distinctes"
                fill={color}
                radius={horizontal ? [0, 5, 5, 0] : [5, 5, 0, 0]}
                maxBarSize={44}
              >
                {!horizontal &&
                  rows.map((row) => (
                    <Cell
                      key={`${row.category}-${row.category_is_missing}`}
                      fill={row.category_is_missing ? '#9aa7b5' : color}
                    />
                  ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </article>
  )
}
