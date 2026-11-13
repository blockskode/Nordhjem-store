import { useEffect, useState } from 'react'
import { browseProducts, searchProducts } from './api'
import { ExplainPanel } from './components/ExplainPanel'
import { Filters } from './components/Filters'
import { ProductCard } from './components/ProductCard'
import { SearchBar } from './components/SearchBar'
import { CATEGORY_LABELS, formatPrice } from './format'
import type { Category, ProductHit, SearchResponse } from './types'

const PAGE_SIZE = 24
const MAX_SEARCH_RESULTS = 96

const SUGGESTIONS = [
  'soft grey sofa',
  'mattress for back pain',
  'wool rug for the living room',
  'garden bench in teak',
]

type Status = 'loading' | 'more' | 'done' | 'error'

interface SearchInfo {
  engine: string
  tookMs: number
  asked: number
  fromWords: string[] // filters read from the words, not clicked
}

/** Describe the filters the API read from the words (not clicked). */
function filtersFromWords(
  applied: SearchResponse['filters'],
  clickedCategory?: Category,
  clickedPrice?: number,
): string[] {
  const found: string[] = []
  if (applied.category && clickedCategory === undefined) {
    found.push(CATEGORY_LABELS[applied.category])
  }
  if (applied.colour) {
    found.push(applied.colour)
  }
  if (applied.max_price && clickedPrice === undefined) {
    found.push(`up to ${formatPrice(applied.max_price)}`)
  }
  return found
}

const EXPLAIN_KEY = 'nordhjem-explain'

/** Read whether Explain was left on last time (false if storage fails). */
function explainWasOn(): boolean {
  try {
    return window.localStorage.getItem(EXPLAIN_KEY) === 'on'
  } catch {
    return false
  }
}

/** Remember the Explain switch for next time; ignore storage errors. */
function rememberExplain(on: boolean) {
  try {
    window.localStorage.setItem(EXPLAIN_KEY, on ? 'on' : 'off')
  } catch {
    // private window or blocked storage: the switch still works
  }
}

/** Put the search text in the address bar, or remove it when browsing. */
function saveQueryInUrl(query: string) {
  const url = query ? `?q=${encodeURIComponent(query)}` : window.location.pathname
  window.history.replaceState(null, '', url)
}

export default function App() {
  const [query, setQuery] = useState('') // empty means browsing
  const [category, setCategory] = useState<Category>()
  const [maxPrice, setMaxPrice] = useState<number>()
  const [status, setStatus] = useState<Status>('loading')
  const [products, setProducts] = useState<ProductHit[]>([])
  const [total, setTotal] = useState(0) // catalogue size when browsing
  const [searchInfo, setSearchInfo] = useState<SearchInfo>()
  const [explain, setExplain] = useState(explainWasOn)
  const [overFilters, setOverFilters] = useState(false) // hovered or focused

  /** Show the first page of the catalogue (no search). */
  async function browse(c?: Category, p?: number) {
    setQuery('')
    saveQueryInUrl('')
    setStatus('loading')
    try {
      const reply = await browseProducts({
        category: c, max_price: p, offset: 0, limit: PAGE_SIZE,
      })
      setProducts(reply.results)
      setTotal(reply.total)
      setSearchInfo(undefined)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  /** Search, asking the API for `asked` results. */
  async function search(q: string, c?: Category, p?: number, asked = PAGE_SIZE) {
    setQuery(q)
    saveQueryInUrl(q)
    setStatus(asked > PAGE_SIZE ? 'more' : 'loading')
    try {
      const reply = await searchProducts({
        query: q, category: c, max_price: p, k: asked,
      })
      setProducts(reply.results)
      setSearchInfo({
        engine: reply.engine,
        tookMs: reply.took_ms,
        asked,
        fromWords: filtersFromWords(reply.filters, c, p),
      })
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  /** Add the next page: more search results, or the next catalogue page. */
  async function showMore() {
    if (query) {
      search(query, category, maxPrice, products.length + PAGE_SIZE)
      return
    }
    setStatus('more')
    try {
      const reply = await browseProducts({
        category, max_price: maxPrice, offset: products.length, limit: PAGE_SIZE,
      })
      setProducts([...products, ...reply.results])
      setTotal(reply.total)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  /** Run the current mode again after a filter changes. */
  function refresh(c?: Category, p?: number) {
    if (query) search(query, c, p)
    else browse(c, p)
  }

  // On first load: search from the address bar (?q=...), or browse.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('q')
    if (q) search(q)
    else browse()
  }, [])

  const canShowMore = searchInfo
    ? products.length === searchInfo.asked && searchInfo.asked < MAX_SEARCH_RESULTS
    : products.length < total

  return (
    <>
      <header className="top">
        <div className="logo">NORDHJEM</div>
        <div className="tagline">Furniture for a calm home</div>
      </header>

      <main>
        <section className="hero">
          <h1>What are you looking for?</h1>
        </section>

        <div className="sticky-search">
          <div className="search-row">
            <SearchBar
              key={query}
              initial={query}
              busy={status === 'loading'}
              onSearch={(q) => search(q, category, maxPrice)}
            />
            <button
              className={explain ? 'explain-toggle on' : 'explain-toggle'}
              aria-pressed={explain}
              title="Show what the page does in code"
              onClick={() => {
                rememberExplain(!explain)
                setExplain(!explain)
              }}
            >
              Explain
            </button>
          </div>
          <div
            className="filter-zone"
            onMouseEnter={() => setOverFilters(true)}
            onMouseLeave={() => setOverFilters(false)}
            onFocus={() => setOverFilters(true)}
            onBlur={(event) => {
              if (!event.currentTarget.contains(event.relatedTarget)) setOverFilters(false)
            }}
          >
            <Filters
              category={category}
              maxPrice={maxPrice}
              onCategory={(c) => {
                setCategory(c)
                refresh(c, maxPrice)
              }}
              onMaxPrice={(p) => {
                setMaxPrice(p)
                refresh(category, p)
              }}
            />
            {explain && overFilters && (
              <ExplainPanel category={category} maxPrice={maxPrice} />
            )}
          </div>
        </div>

        {!query && (
          <div className="suggestions">
            <span>Try:</span>
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => search(s, category, maxPrice)}>
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="info">
          {searchInfo ? (
            <span>
              {products.length} results for "{query}" · {searchInfo.tookMs} ms ·{' '}
              {searchInfo.fromWords.length > 0 && (
                <>
                  <span className="from-words" title="Filters read from your words">
                    filtered by your words: {searchInfo.fromWords.join(', ')}
                  </span>{' '}
                  ·{' '}
                </>
              )}
              <button className="link" onClick={() => browse(category, maxPrice)}>
                Clear search
              </button>
            </span>
          ) : (
            <span>
              Showing {products.length} of {total} products
            </span>
          )}
          {searchInfo && (
            <span className="engine" title="Which search code answered">
              {searchInfo.engine}
            </span>
          )}
        </div>

        {status === 'error' && (
          <p className="message" role="alert">
            Something went wrong. Please try again.
          </p>
        )}

        {status === 'done' && products.length === 0 && (
          <p className="message">
            No products found. Try other words or remove a filter.
          </p>
        )}

        <div className={status === 'loading' ? 'grid dim' : 'grid'}>
          {products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>

        {canShowMore && status !== 'error' && (
          <div className="more">
            <button onClick={showMore} disabled={status === 'more'}>
              {status === 'more' ? 'Loading' : 'Show more'}
            </button>
          </div>
        )}
      </main>
    </>
  )
}
