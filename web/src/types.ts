// The shapes of the /api/search request and reply.
// They mirror api/models.py; change both together.

export type Category =
  | 'sofa'
  | 'mattress'
  | 'rug'
  | 'dining_table'
  | 'office_chair'
  | 'garden'
  | 'pillow'
  | 'duvet'

export interface SearchRequest {
  query: string
  category?: Category
  max_price?: number
  k?: number
}

export interface ProductHit {
  product_id: string
  name: string
  category: Category
  colour: string
  price_dkk: number
  image_url: string
  score: number | null
}

export interface BrowseRequest {
  category?: Category
  max_price?: number
  offset: number
  limit: number
}

export interface BrowseResponse {
  results: ProductHit[]
  total: number
}

export interface SearchResponse {
  results: ProductHit[]
  engine: string
  took_ms: number
  /** The filters applied: clicked, or read from the words. */
  filters: { category: Category | null; max_price: number | null }
}
