import { useEffect, useState } from 'react'
import { browseProducts } from '../api'
import { formatPrice } from '../format'
import type { Category, ProductHit } from '../types'

const PAGE = 96 // the most the browse endpoint returns at once

interface Props {
  category?: Category
  maxPrice?: number
}

/** One row of the sample table: a product and its True/False answers. */
interface Row {
  product: ProductHit
  categoryOk: boolean | null // null: the category filter is not set
  priceOk: boolean | null // null: the price filter is not set
  passes: boolean
}

let catalogue: Promise<ProductHit[]> | undefined

/** Load all products once (a few pages of the browse endpoint). */
function loadCatalogue(): Promise<ProductHit[]> {
  if (!catalogue) {
    catalogue = (async () => {
      const first = await browseProducts({ offset: 0, limit: PAGE })
      const all = [...first.results]
      while (all.length < first.total) {
        const next = await browseProducts({ offset: all.length, limit: PAGE })
        all.push(...next.results)
      }
      return all
    })()
    catalogue.catch(() => {
      catalogue = undefined // try again next time
    })
  }
  return catalogue
}

/** The same rule as filter_products in api/search.py, for one product. */
function check(product: ProductHit, category?: Category, maxPrice?: number): Row {
  const categoryOk = category === undefined ? null : product.category === category
  const priceOk = maxPrice === undefined ? null : product.price_dkk <= maxPrice
  return { product, categoryOk, priceOk, passes: categoryOk !== false && priceOk !== false }
}

/**
 * Pick up to 4 products that show each case: passes both, fails the
 * category, fails the price, fails both. Products are visited in a
 * spread-out order so the samples come from different categories.
 */
function pickSamples(products: ProductHit[], category?: Category, maxPrice?: number): Row[] {
  const rows = products.map((_, i) => products[(i * 97) % products.length])
    .map((p) => check(p, category, maxPrice))
  const wanted: Array<(r: Row) => boolean> = [
    (r) => r.passes,
    (r) => r.categoryOk === false && r.priceOk !== false,
    (r) => r.categoryOk !== false && r.priceOk === false,
    (r) => r.categoryOk === false && r.priceOk === false,
  ]
  const picked: Row[] = []
  for (const test of wanted) {
    const row = rows.find((r) => test(r) && !picked.includes(r))
    if (row) picked.push(row)
  }
  for (const row of rows) {
    if (picked.length >= 4) break
    if (!picked.includes(row) && !picked.some((p) => p.product.category === row.product.category)) {
      picked.push(row)
    }
  }
  return picked
}

/** How Python would print the SearchFilters instance. */
function filtersRepr(category?: Category, maxPrice?: number): string {
  const c = category === undefined ? 'None' : `'${category}'`
  const p = maxPrice === undefined ? 'None' : maxPrice.toFixed(1)
  return `SearchFilters(category=${c}, max_price=${p})`
}

/** A True/False cell, or "skipped" when that filter is not set. */
function Cell({ value }: { value: boolean | null }) {
  if (value === null) return <td className="x-skip">skipped</td>
  return <td className={value ? 'x-true' : 'x-false'}>{value ? 'True' : 'False'}</td>
}

/** Explain piece 1: what the filter controls become, and what filter_products does. */
export function ExplainPanel({ category, maxPrice }: Props) {
  const [products, setProducts] = useState<ProductHit[]>()
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    loadCatalogue().then(setProducts).catch(() => setFailed(true))
  }, [])

  const categoryHead = category === undefined ? 'category' : `== '${category}'`
  const priceHead = maxPrice === undefined ? 'price' : `<= ${maxPrice}`

  let body
  if (failed) {
    body = <p className="x-note">Could not load the products.</p>
  } else if (!products) {
    body = <p className="x-note">Loading the 500 products</p>
  } else {
    const rows = pickSamples(products, category, maxPrice)
    const all = products.map((p) => check(p, category, maxPrice))
    const afterCategory = all.filter((r) => r.categoryOk !== false).length
    const afterBoth = all.filter((r) => r.passes).length
    body = (
      <>
        <h3>
          2 · <code>filter_products(index, filters)</code> on 4 of the products
        </h3>
        <div className="x-scroll">
          <table className="x-table">
            <thead>
              <tr>
                <th>product</th>
                <th>category</th>
                <th className="x-num">price</th>
                <th><code>{categoryHead}</code></th>
                <th><code>{priceHead}</code></th>
                <th className="x-result"><code>&amp;</code> returned</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.product.product_id}>
                  <td>{r.product.name}</td>
                  <td>{r.product.category}</td>
                  <td className="x-num">{formatPrice(r.product.price_dkk)}</td>
                  <Cell value={r.categoryOk} />
                  <Cell value={r.priceOk} />
                  <td className={r.passes ? 'x-result x-true' : 'x-result x-false'}>
                    {r.passes ? 'True' : 'False'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>3 · On all {products.length} products</h3>
        <ol className="x-steps">
          <li>
            <code>np.ones(...)</code> <span>{products.length} True</span>
          </li>
          <li>
            <code>&amp; {category === undefined ? 'category not set: skipped' : `(categories == '${category}')`}</code>{' '}
            <span>{afterCategory} True</span>
          </li>
          <li>
            <code>&amp; {maxPrice === undefined ? 'max price not set: skipped' : `(prices <= ${maxPrice})`}</code>{' '}
            <span className="x-final">{afterBoth} True</span>
          </li>
        </ol>
        <p className="x-note">
          Only these {afterBoth} can appear in the results. Every other product gets the
          score <code>-inf</code> in <code>search()</code>.
        </p>
      </>
    )
  }

  return (
    <div className="explain-panel" role="note" aria-label="Explain the filters">
      <h3>1 · What your choices become</h3>
      <pre className="x-code">filters = {filtersRepr(category, maxPrice)}</pre>
      {body}
    </div>
  )
}
