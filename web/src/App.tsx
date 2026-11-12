import { useEffect, useState } from 'react'
import { browseProducts, searchProducts } from './api'
import { Filters } from './components/Filters'
import { ProductCard } from './components/ProductCard'
import { SearchBar } from './components/SearchBar'
import type { Category, ProductHit } from './types'

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
      setSearchInfo({ engine: reply.engine, tookMs: reply.took_ms, asked })
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
          <SearchBar
            key={query}
            initial={query}
            busy={status === 'loading'}
            onSearch={(q) => search(q, category, maxPrice)}
          />
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
