import { useEffect, useRef, useState } from 'react'
import { askPolicy } from '../api'
import type { Country, Source, Topic } from '../types'

const COUNTRIES: { code: Country; label: string }[] = [
  { code: 'DK', label: 'Denmark' },
  { code: 'SE', label: 'Sweden' },
  { code: 'NO', label: 'Norway' },
  { code: 'DE', label: 'Germany' },
]

const TOPICS: { code: Topic; label: string }[] = [
  { code: 'returns', label: 'Returns' },
  { code: 'delivery', label: 'Delivery' },
  { code: 'warranty', label: 'Warranty' },
  { code: 'payment', label: 'Payment' },
  { code: 'orders', label: 'Orders' },
  { code: 'shop', label: 'Shop' },
]

const COUNTRY_KEY = 'nordhjem-country'

interface Message {
  from: 'customer' | 'shop'
  text: string
  sources?: Source[]
  engine?: string
  failed?: boolean
}

/** Read the remembered country; Denmark if none or storage is blocked. */
function savedCountry(): Country {
  try {
    const value = localStorage.getItem(COUNTRY_KEY)
    if (COUNTRIES.some((c) => c.code === value)) return value as Country
  } catch {
    // storage blocked: use the default
  }
  return 'DK'
}

/** The policy chat: a dialog in the middle of the page. */
export function ChatDialog({ onClose }: { onClose: () => void }) {
  const [country, setCountry] = useState<Country>(savedCountry)
  const [topic, setTopic] = useState<Topic>()
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [waiting, setWaiting] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => {
    input.current?.focus()
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, waiting])

  function chooseCountry(value: Country) {
    setCountry(value)
    try {
      localStorage.setItem(COUNTRY_KEY, value)
    } catch {
      // storage blocked: the choice lasts for this visit only
    }
  }

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const question = text.trim()
    if (!question || waiting) return
    setText('')
    setMessages((m) => [...m, { from: 'customer', text: question }])
    setWaiting(true)
    try {
      const reply = await askPolicy({ question, country, topic })
      setMessages((m) => [
        ...m,
        {
          from: 'shop',
          text: reply.answer,
          sources: reply.sources,
          engine: reply.engine,
        },
      ])
    } catch {
      setMessages((m) => [
        ...m,
        { from: 'shop', text: 'Something went wrong. Please try again.', failed: true },
      ])
    } finally {
      setWaiting(false)
      input.current?.focus()
    }
  }

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <section className="chat-dialog" role="dialog" aria-modal="true" aria-label="Ask Nordhjem">
        <div className="chat-inner">
          <header className="chat-head">
            <h2>Ask Nordhjem</h2>
            <button className="close" onClick={onClose} aria-label="Close">
              ×
            </button>
          </header>

          <div className="chat-setup">
            <label>
              Country{' '}
              <select
                value={country}
                onChange={(e) => chooseCountry(e.target.value as Country)}
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="chips" role="group" aria-label="Topic">
              <button
                className={topic === undefined ? 'chip on' : 'chip'}
                aria-pressed={topic === undefined}
                onClick={() => setTopic(undefined)}
              >
                All topics
              </button>
              {TOPICS.map((t) => (
                <button
                  key={t.code}
                  className={topic === t.code ? 'chip on' : 'chip'}
                  aria-pressed={topic === t.code}
                  onClick={() => setTopic(t.code)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="msgs" aria-live="polite">
            {messages.length === 0 && (
              <p className="hint">
                Ask about returns, delivery, warranty, payment or your order.
                For example: "Can I return a mattress after 80 nights?"
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.from === 'customer' ? 'msg me' : m.failed ? 'msg bot failed' : 'msg bot'}>
                <p>{m.text}</p>
                {m.sources && m.sources.length > 0 && (
                  <p className="src">
                    Source: {m.sources.map((s) => s.title).join(', ')}
                  </p>
                )}
                {m.engine && <p className="engine-tag">{m.engine}</p>}
              </div>
            ))}
            {waiting && (
              <div className="msg bot">
                <span className="dots" aria-label="Answering">
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            )}
            <div ref={end} />
          </div>

          <form className="chat-input" onSubmit={send}>
            <input
              ref={input}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ask about returns, delivery, warranty…"
              maxLength={500}
              aria-label="Your question"
            />
            <button type="submit" disabled={waiting || !text.trim()}>
              Send
            </button>
          </form>
        </div>
      </section>
    </>
  )
}
