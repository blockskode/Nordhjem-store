import { useState, type FormEvent } from 'react'

interface Props {
  initial: string
  busy: boolean
  onSearch: (query: string) => void
}

/** The search box and its button. Calls onSearch with the trimmed text. */
export function SearchBar({ initial, busy, onSearch }: Props) {
  const [text, setText] = useState(initial)

  function submit(event: FormEvent) {
    event.preventDefault()
    const query = text.trim()
    if (query) onSearch(query)
  }

  return (
    <form className="search" onSubmit={submit} role="search">
      <input
        aria-label="Search products"
        placeholder="Try: soft grey sofa, mattress for back pain"
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <button type="submit" disabled={busy || !text.trim()}>
        {busy ? 'Searching' : 'Search'}
      </button>
    </form>
  )
}
