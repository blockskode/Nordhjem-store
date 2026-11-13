/** An empty card with a soft shimmer, shown while results load. */
export function SkeletonCard() {
  return (
    <div className="card skeleton" aria-hidden="true">
      <div className="photo shimmer" />
      <div className="card-body">
        <div className="bone shimmer short" />
        <div className="bone shimmer" />
        <div className="bone shimmer price-bone" />
      </div>
    </div>
  )
}
