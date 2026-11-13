# Handoff

Last updated 2026-11-12. A new session starts here: read this file,
then `PLAN.md`, then do **"Start here"** below.

## The project in three lines

Nordhjem is a fictional Scandinavian furniture store. We build its
website and an AI assistant on Firebase and Google Cloud in four
phases (search, RAG, agent, later a GNN). It is also the owner's
preparation for a **JYSK AI Engineer interview around 2026-11-17**;
the owner's weak spots are AI agents and RAG / embeddings / semantic
search, so those come first and as deep as possible.

## Start here (the exact next action)

**Phase 2, Step 2: RAG over policies** (`PLAN.md`, Step 2). Not
started. Needs first (Claude, plumbing): about 20 policy documents with
the traps (old and new version, country differences, a question with
no answer), a loader that chunks and embeds them into Firestore, an
evaluation set, then the exercise (`api/rag.py`, owner) with learn PDF,
check and reference. Design it with the owner first, one piece at a
time.

Done (2026-11-13):
- **Step 1, semantic search**: the owner's `api/search.py` passes
  (meaning 1.00 / 0.99, language 1.00 / 0.96). The owner renamed
  `allowed` to `filter_products`, `embed_query` to `get_embed_query`,
  `top_k` to `get_top_k`; `check.py` and `solution.py` follow.
- **Step 1b, filters from the words** (`steps/01b_filters_from_words/`):
  the owner's `api/parse_query.py` (ParsedQuery, merge_filters,
  INSTRUCTION, parse_query with `gemini-3-flash-preview`, structured
  output) passes 15 of 15 sentences; "sofa under 4000 kr" goes from
  precision 0.00 to 1.00. `api/app.py` reads filters before searching
  and falls back safely; the page shows "filtered by your words".
- **Explain mode, piece 1** on the page: a toggle next to Search; hover
  the filters to see `SearchFilters(...)`, a 4-product
  `filter_products` table and the counts on all 500. Add one piece per
  concept the owner covers (next candidate: scores and top-k).
- `steps/01_embeddings/notes.pdf`: queries vs documents, what the score
  means, where filters come from (Latin Modern, thesis style).

Known: each new search takes about 3 to 5 s (one Gemini call to read
the filters, plus a cold start). Cheap fix offered for later: skip the
call when the text has no number and no category word.

Offered, not decided: mix categories in the browse order. The
architecture PDF was postponed by the owner.

### Live now (2026-11-13)

- Site: https://nordhjemstore.web.app (React + TypeScript + Vite in
  `web/`, look "Linen and terracotta": bg `#F6F1EA`, ink `#2E2622`,
  accent `#B5583A`). Browse 24 at a time, category chips, max price,
  sticky search bar, `?q=` in the address, Explain toggle.
- API: Cloud Run `nordhjem-api` (europe-west1, max 3 instances,
  public, service account `nordhjem-api@` with `roles/datastore.user`
  and `roles/aiplatform.user`),
  https://nordhjem-api-757427498119.europe-west1.run.app. Routes:
  `GET /api/health`, `POST /api/search` (the owner's semantic search,
  filters read from the words; reply includes the `filters` applied),
  `GET /api/products` (browse), `GET /api/products/{id}`.
- Photos: 125 in `gs://nordhjemstore.firebasestorage.app/product-images/`.
- Rules: Firestore denies all browser access; Storage allows public
  read of `product-images/` only.
- Architecture diagrams: `docs/diagrams/` (TikZ source, PDF, PNG):
  overview v5, search flow, RAG flow, agent, data model.

### How to run and deploy

- Local: `uv run uvicorn api.app:app --reload --port 8000` (repo
  root) and `npm run dev` in `web/` (Vite forwards /api and /images).
- API: `gcloud run deploy nordhjem-api --source . --region
  europe-west1 --project nordhjemstore --quiet` keeps the existing
  settings. The permission check sometimes blocks it for Claude; the
  owner then runs it with `!`. The first deploy used (full command in git history
  of this file's commit, or: region europe-west1, service account
  above, `--max-instances 3 --memory 512Mi`, env
  `IMAGE_URL_TEMPLATE=https://firebasestorage.googleapis.com/v0/b/nordhjemstore.firebasestorage.app/o/product-images%2F{file}?alt=media`).
- Page: `npm run build` in `web/`, then `firebase deploy --only hosting`.
- Rules: `firebase deploy --only firestore:rules,storage`.

## How the owner works (important)

- **The owner writes the core code** (search, RAG, agent, model).
  Claude prepares: a learn PDF, an exercise skeleton with TODOs, a
  check script that tests it, and a reference solution kept separate.
  Setup and plumbing (GCP, Firebase, data generation, the web shell)
  Claude may do, and says that it did. The owner once said "i need to
  practice" when Claude did everything, then "it ok to setup up the
  project. this is the easies part. now let do the real exerice".
- **Teach in depth, never jump.** Build each concept: the problem, the
  idea, one worked example with real numbers, every math step shown
  (definition, substitution, each product, each sum, result), the
  traps, then the exercise. The owner said "be precise", "don't jump"
  when a squaring step was skipped. Verify every number in code before
  it goes into a document.
- **Learn material as LaTeX PDFs**, not markdown (easier to read).
  Built with `tectonic`; earlier style: TeX Gyre Pagella and Heros,
  loaded by file name (`texgyrepagella` with `Extension=.otf`), one teal
  accent `#2A7D78`. Render pages with
  `uv run --with pymupdf` to check them before showing.
- **Tables do not go in the terminal**; wide tables are hard to read
  there. Concept answers with tables go into a running reference PDF
  (`notes.tex` -> `notes.pdf`, to start in this repo), with a short
  chat reply.
- Simple words, short sentences, explain each term where it appears.
  **No em dashes** in anything written for the owner.
- Show visual work (page, colours) before committing; offer at least
  five rendered options for look and colour choices.
- Python: PEP 8, type hints and a docstring on every function, simple
  over clever.
- Commit and push after an approved change; plain
  `git commit -m "message"`, stage specific files.

## What the owner already knows (from Step 1 in the old repo)

The owner did part of Step 1 before the move, in
`/Users/yapi.donatien.achou/practice/jysk-ai-engineer/` (kept only as
a reference; its code is **not** reused, this repo starts from
scratch).

- Understood: embeddings as vectors, dot product, L2 norm (with the
  squaring step), cosine similarity (1 same direction, 0 unrelated,
  -1 opposite), normalising to length 1, the search idea (embed the
  question, compare with every product vector, sort, return the
  closest), ADC vs API key, what Vertex AI is, its mapping to MLflow
  on Databricks.
- Did: Exercise A questions 1 and 2 (one embedding call; the vector
  has 3072 numbers and length about 1). Was at question 3 (batching
  2, 50 and 250 texts per call) and question 4 (timing).
- Not done: Exercise B (writing `search()` and measuring hit@5 and
  precision@5).
- Useful reference files there: `steps/01_embeddings/learn.pdf` (the
  Step 1 learn PDF), `notes.pdf` (GCP basics, ADC, Vertex vs MLflow,
  norms), `steps/01_embeddings/solution.py` (reference search; scored
  meaning 1.00 / 0.99, language 1.00 / 0.96 on hit@5 / precision@5).
  Reuse the PDFs' content where it fits instead of rewriting it.

## What is in this repo

| Path | What |
|---|---|
| `PLAN.md` | the four-phase plan |
| `firebase_config.js` | Firebase web config for project `nordhjemstore` |
| `data/products.jsonl` | 500 products, one JSON object per line |
| `data/eval/product_queries.json` | 23 search test questions with the relevant product IDs |
| `data/images/` | 125 product photos (JPEG, 4:3, max 1200 px), about 34 MB |
| `data/product_images.json` | product ID to photo file name, 500 entries |

Product fields: `product_id` (P1001 to P1500), `name`, `category`
(mattress, sofa, rug, garden, pillow, duvet, dining_table,
office_chair), `colour`, `price_dkk`, `language` (en 343, da 107,
de 50), `description`, `attributes` (depend on the category).
Test question kinds: `meaning`, `language`, `needs_filter` (the last
cannot be answered by embeddings alone, on purpose; Step 3 fixes it
with filters).

## Decisions so far

- Goal: all four phases; if time runs out before the interview,
  continue after it.
- Everything runs in the Firebase project `nordhjemstore`: page on
  Firebase Hosting, products in Firestore, photos in Cloud Storage
  for Firebase, the AI service (Python) on Cloud Run behind a Hosting
  rewrite on `/api/...`.
- Fictional brand Nordhjem; no JYSK name, logo or look.
- Phase 4 (GNN) is to be discussed later. First idea: weekly demand
  forecast reusing `~/semcon/gnn` (`src/models/gnn_base.py`).
- Front end: React + TypeScript + Vite (owner, 2026-11-12).
- Look: "Linen and terracotta" (owner chose variant 3 of 7).
- Diagram style: no orange bar on the hub; right-angle arrows;
  cylinders for data stores.

## Things to know

- The data has no generator script here: it is a fixed dataset. Do
  not delete it.
- Vertex AI from Python (package `google-genai`):
  `genai.Client(vertexai=True, project=..., location=...)`. Without
  `vertexai=True` it asks for an API key.
  - Embeddings: `gemini-embedding-001` in `europe-west1`. 3072 numbers
    by default, already length 1; `output_dimensionality=768` for
    shorter vectors. Up to 250 texts per call.
  - Gemini: `gemini-3-flash-preview`, only in location `global`. Older
    names like `gemini-2.5-flash` were not available to a new project.
  - Images: `gemini-3-pro-image` in `global` via `generate_content`
    with `response_modalities=["IMAGE"]`. Imagen models returned 404.
    More than 2 parallel requests gave 429 (rate limit).
  These were found on the old project; recheck on `nordhjemstore`.
- Python environments: make the venv with `uv venv` in this repo. A uv
  venv has no pip; add it with `.venv/bin/python -m ensurepip` if the
  owner wants `pip install`. The owner once had another venv
  (`practice`) active, which gave `cannot import name 'genai'`; check
  with `which python3`.
- Firebase web `apiKey` values identify the project; they are not
  secrets. Protection comes from Firestore and Storage security rules
  (and optionally App Check), written before anything goes public.
- Cost: never leave running Vertex AI Vector Search endpoints, GPU
  machines or Agent Engine deployments.
