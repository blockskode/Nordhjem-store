import type { Category } from './types'

const PRICE = new Intl.NumberFormat('da-DK', { maximumFractionDigits: 0 })

/** 3259 -> "3.259 kr." (Danish style). */
export function formatPrice(priceDkk: number): string {
  return `${PRICE.format(priceDkk)} kr.`
}

export const CATEGORY_LABELS: Record<Category, string> = {
  sofa: 'Sofa',
  mattress: 'Mattress',
  rug: 'Rug',
  dining_table: 'Dining table',
  office_chair: 'Office chair',
  garden: 'Garden',
  pillow: 'Pillow',
  duvet: 'Duvet',
}
