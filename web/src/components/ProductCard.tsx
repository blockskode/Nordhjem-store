import { CATEGORY_LABELS, formatPrice } from '../format'
import type { ProductHit } from '../types'

/** One product: photo, category and colour, name, price and score. */
export function ProductCard({ product }: { product: ProductHit }) {
  return (
    <article className="card">
      <div className="photo">
        <img src={product.image_url} alt={product.name} loading="lazy" />
      </div>
      <div className="card-body">
        <div className="meta">
          {CATEGORY_LABELS[product.category]} · {product.colour}
        </div>
        <h3 className="name">{product.name}</h3>
        <div className="row">
          <span className="price">{formatPrice(product.price_dkk)}</span>
          {product.score !== null && (
            <span className="score" title="Similarity score from the search">
              score {product.score.toFixed(2)}
            </span>
          )}
        </div>
      </div>
    </article>
  )
}
