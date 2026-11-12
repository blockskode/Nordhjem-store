import type {
  BrowseRequest,
  BrowseResponse,
  SearchRequest,
  SearchResponse,
} from './types'

/** Ask the API for products that match the request. Throws on any error. */
export async function searchProducts(
  request: SearchRequest,
): Promise<SearchResponse> {
  const response = await fetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Search failed with status ${response.status}`)
  }
  return (await response.json()) as SearchResponse
}

/** Get one page of the catalogue, without a search. Throws on any error. */
export async function browseProducts(
  request: BrowseRequest,
): Promise<BrowseResponse> {
  const params = new URLSearchParams({
    offset: String(request.offset),
    limit: String(request.limit),
  })
  if (request.category) params.set('category', request.category)
  if (request.max_price) params.set('max_price', String(request.max_price))
  const response = await fetch(`/api/products?${params}`)
  if (!response.ok) {
    throw new Error(`Browse failed with status ${response.status}`)
  }
  return (await response.json()) as BrowseResponse
}
