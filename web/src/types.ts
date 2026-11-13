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
  filters: {
    category: Category | null
    colour: string | null
    max_price: number | null
  }
}

// ---- the policy chat (Step 2) ----

export type Country = 'DK' | 'SE' | 'NO' | 'DE'
export type Topic =
  | 'returns'
  | 'delivery'
  | 'warranty'
  | 'payment'
  | 'orders'
  | 'shop'

/** Body of POST /api/ask. Mirrors AskRequest in api/models.py. */
export interface AskRequest {
  question: string
  country: Country
  topic?: Topic
}

export interface Source {
  doc_id: string
  title: string
}

/** Reply of POST /api/ask. Mirrors AskResponse in api/models.py. */
export interface AskResponse {
  answer: string
  sources: Source[]
  engine: string
  took_ms: number
}
