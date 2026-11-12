import { CATEGORY_LABELS, formatPrice } from '../format'
import type { Category } from '../types'

const MAX_PRICES = [1000, 2500, 5000, 10000]

interface Props {
  category?: Category
  maxPrice?: number
  onCategory: (category?: Category) => void
  onMaxPrice: (maxPrice?: number) => void
}

/** Category chips and a max-price choice. Undefined means "any". */
export function Filters({ category, maxPrice, onCategory, onMaxPrice }: Props) {
  const categories = Object.keys(CATEGORY_LABELS) as Category[]

  return (
    <div className="filters">
      <div className="chips" role="group" aria-label="Category">
        <button
          className={category === undefined ? 'chip on' : 'chip'}
          onClick={() => onCategory(undefined)}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c}
            className={category === c ? 'chip on' : 'chip'}
            onClick={() => onCategory(c)}
          >
            {CATEGORY_LABELS[c]}
          </button>
        ))}
      </div>
      <label className="price-filter">
        Max price
        <select
          value={maxPrice ?? ''}
          onChange={(event) =>
            onMaxPrice(event.target.value ? Number(event.target.value) : undefined)
          }
        >
          <option value="">Any</option>
          {MAX_PRICES.map((p) => (
            <option key={p} value={p}>
              {formatPrice(p)}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
