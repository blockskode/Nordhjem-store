# Handoff

Last updated 2026-11-12. Read `PLAN.md` first.

## Where things stand

This repo starts from scratch. Only the data came over from the
earlier work (`/Users/yapi.donatien.achou/practice/jysk-ai-engineer/`,
which stays there as a reference and is not part of this project).

What is here:

| Path | What |
|---|---|
| `PLAN.md` | the four-phase plan |
| `firebase_config.js` | Firebase web config for project `nordhjemstore` |
| `data/products.jsonl` | 500 products, one JSON object per line |
| `data/eval/product_queries.json` | 23 search test questions with the relevant product IDs |
| `data/images/` | 125 product photos (JPEG, 4:3, max 1200 px), about 32 MB |
| `data/product_images.json` | product ID to photo file name, 500 entries |

Product fields: `product_id` (P1001 to P1500), `name`, `category`,
`colour`, `price_dkk`, `language` (en, da, de), `description`,
`attributes` (depend on the category).

## Next steps

1. Confirmed 2026-11-12: everything runs in the `nordhjemstore`
   project, on Firebase Hosting + Firestore + Storage + Cloud Run.
2. Set up `nordhjemstore` for that: Blaze plan, APIs, budget alert (Claude may do the setup; the
   owner writes the core code).
3. Phase 1: the store page and product search, with a learn PDF,
   exercise, reference solution and check.

## Things to know

- The data has no generator script here: it is a fixed dataset. Do
  not delete it.
- Vertex AI from Python: `genai.Client(vertexai=True, project=...,
  location=...)`; without `vertexai=True` it asks for an API key.
  Embeddings `gemini-embedding-001` in `europe-west1`; Gemini
  `gemini-3-flash-preview` and images `gemini-3-pro-image` only in
  `global`.
- Firebase web `apiKey` values identify the project; they are not
  secrets. Protection comes from Firestore and Storage security rules
  (and optionally App Check), so those must be written before going
  public.
- Commit and push after approved changes; no em dashes in documents.
